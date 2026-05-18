import asyncio
import random
from loguru import logger
from urllib.parse import urlencode


LINKEDIN_JOBS_URL = "https://www.linkedin.com/jobs/search/"


class LinkedInScraper:
    async def search(self, page, prefs: dict, limit: int = 10) -> list[dict]:
        jobs = []
        roles = prefs.get("desired_roles", ["Software Engineer"])
        locations = prefs.get("locations", [""])
        remote = prefs.get("remote_preference", "remote")

        for role in roles[:2]:
            for location in locations[:1]:
                params = {"keywords": role, "location": location or ""}
                if remote in ("remote", "hybrid"):
                    params["f_WT"] = "2"

                url = LINKEDIN_JOBS_URL + "?" + urlencode(params)
                logger.info(f"[scraper] navigating to {url}")
                await page.goto(url, wait_until="domcontentloaded", timeout=20000)
                await asyncio.sleep(random.uniform(2, 4))

                logger.info(f"[scraper] landed on {page.url}")

                batch = await self._extract_jobs(page, limit - len(jobs))
                logger.info(f"[scraper] extracted {len(batch)} jobs for role={role}")
                jobs.extend(batch)
                if len(jobs) >= limit:
                    break

        return jobs[:limit]

    async def _extract_jobs(self, page, limit: int) -> list[dict]:
        jobs = []
        try:
            # Wait for job list items to appear
            try:
                await page.wait_for_selector(
                    "li[data-occludable-job-id], li.jobs-search-results__list-item, .job-search-card",
                    timeout=8000
                )
            except Exception:
                pass

            # Scroll through results to trigger lazy rendering of occluded cards
            results_list = page.locator("ul.jobs-search__results-list, div.jobs-search-results-grid__list, div[class*='jobs-search-results']").first
            if await results_list.count():
                await results_list.evaluate("el => el.scrollTop = el.scrollHeight")
                await asyncio.sleep(1)
                await results_list.evaluate("el => el.scrollTop = 0")
            else:
                # Fallback: scroll the page
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(1)
                await page.evaluate("window.scrollTo(0, 0)")

            await asyncio.sleep(1.5)

            # Pull job data via JavaScript — most reliable way for occluded items
            jobs_data = await page.evaluate("""
                () => {
                    const items = document.querySelectorAll('li[data-occludable-job-id], li.jobs-search-results__list-item');
                    return Array.from(items).map(li => {
                        const titleEl = li.querySelector('a[href*="/jobs/view/"]') ||
                                        li.querySelector('.job-card-list__title--link') ||
                                        li.querySelector('.job-card-list__title') ||
                                        li.querySelector('strong');
                        const companyEl = li.querySelector('.job-card-container__primary-description') ||
                                          li.querySelector('.job-card-container__company-name') ||
                                          li.querySelector('span[class*="subtitle"]');
                        const linkEl = li.querySelector('a[href*="/jobs/view/"]');
                        return {
                            title: titleEl ? titleEl.innerText.trim() : '',
                            company: companyEl ? companyEl.innerText.trim() : '',
                            href: linkEl ? linkEl.href : '',
                        };
                    }).filter(j => j.title && j.href);
                }
            """)

            logger.info(f"[scraper] JS extracted {len(jobs_data)} raw jobs")

            for item in jobs_data[:limit]:
                try:
                    job_url = item["href"].split("?")[0]
                    description = await self._get_description(page, job_url)
                    jobs.append({
                        "title": item["title"],
                        "company": item["company"],
                        "job_url": job_url,
                        "description": description,
                        "portal": "linkedin",
                    })
                    await asyncio.sleep(random.uniform(1, 2))
                except Exception as e:
                    logger.info(f"[scraper] skipped item: {e}")
                    continue

        except Exception as e:
            logger.error(f"[scraper] _extract_jobs error: {e}")
        return jobs

    async def _get_description(self, page, job_url: str) -> str:
        if not job_url:
            return ""
        try:
            detail_page = await page.context.new_page()
            await detail_page.goto(job_url, wait_until="domcontentloaded", timeout=15000)
            await asyncio.sleep(random.uniform(1, 2))
            desc_el = detail_page.locator(
                ".description__text, .jobs-description__content, .job-details-jobs-unified-top-card__job-insight"
            ).first
            desc = await desc_el.inner_text() if await desc_el.count() else ""
            await detail_page.close()
            return desc.strip()[:3000]
        except Exception as e:
            logger.info(f"[scraper] description fetch failed: {e}")
            return ""
