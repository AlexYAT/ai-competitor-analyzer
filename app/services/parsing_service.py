"""Selenium-based page parsing (visible text, meta, screenshot)."""

import re
import uuid
from pathlib import Path

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from app.core.config import Settings
from app.core.exceptions import ParsingError
from app.models.schemas import ParsedPageData

_VISIBLE_TEXT_MAX_CHARS = 18_000


def _normalize_page_url(url: str) -> str:
    u = url.strip()
    if not u:
        raise ParsingError("URL is empty.")
    if not u.startswith(("http://", "https://")):
        u = f"https://{u}"
    return u


def _create_chrome_driver(settings: Settings) -> webdriver.Chrome:
    """Build a Chrome WebDriver from settings (headless, timeouts).

    Requires a matching Chrome / ChromeDriver install on the machine (Selenium 4+
    can resolve the driver via Selenium Manager when possible).
    """
    opts = Options()
    if settings.SELENIUM_HEADLESS:
        opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--lang=en-US")

    driver = webdriver.Chrome(options=opts)
    driver.set_page_load_timeout(int(settings.SELENIUM_PAGELOAD_TIMEOUT))
    return driver


def _clean_visible_text(raw: str) -> str:
    text = re.sub(r"\s+", " ", raw or "").strip()
    if len(text) > _VISIBLE_TEXT_MAX_CHARS:
        return text[:_VISIBLE_TEXT_MAX_CHARS]
    return text


def _meta_description(driver: webdriver.Chrome) -> str | None:
    els = driver.find_elements(By.CSS_SELECTOR, 'meta[name="description"]')
    if not els:
        return None
    content = els[0].get_attribute("content")
    if content is None:
        return None
    c = str(content).strip()
    return c or None


def _first_h1(driver: webdriver.Chrome) -> str | None:
    els = driver.find_elements(By.TAG_NAME, "h1")
    if not els:
        return None
    t = els[0].text.strip()
    return t or None


def parse_page(url: str, settings: Settings) -> ParsedPageData:
    """Load ``url`` in headless Chrome, extract basic fields and save a PNG screenshot.

    Raises:
        ParsingError: If navigation, wait, or extraction fails.
    """
    requested = _normalize_page_url(url)
    out_dir = Path(settings.PARSED_SCREENSHOTS_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    shot_name = f"{uuid.uuid4().hex}.png"
    shot_path = out_dir / shot_name

    driver: webdriver.Chrome | None = None
    try:
        driver = _create_chrome_driver(settings)
        driver.get(requested)

        wait_s = int(settings.SELENIUM_WAIT_TIMEOUT)
        WebDriverWait(driver, wait_s).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        body = driver.find_element(By.TAG_NAME, "body")
        visible = _clean_visible_text(body.text)

        title_el = driver.title or ""
        title = title_el.strip()

        meta_desc = _meta_description(driver)
        h1 = _first_h1(driver)
        final = (driver.current_url or requested).strip()

        driver.save_screenshot(str(shot_path))
        screenshot_rel = str(shot_path).replace("\\", "/")

        return ParsedPageData(
            requested_url=requested,
            final_url=final,
            title=title,
            meta_description=meta_desc,
            h1=h1,
            visible_text=visible,
            screenshot_path=screenshot_rel,
        )
    except TimeoutException as exc:
        raise ParsingError(f"Page load or wait timed out: {exc}") from exc
    except WebDriverException as exc:
        raise ParsingError(f"Browser error: {exc}") from exc
    finally:
        if driver is not None:
            driver.quit()
