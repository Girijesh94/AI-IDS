"""Verify dashboard behavior in a fresh headless browser, with no user profile."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright


def main():
    errors=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',headless=True)
        page=browser.new_page(viewport={'width':1440,'height':1100})
        page.on('pageerror',lambda e:errors.append(str(e)))
        for route in ['/','/operations','/network-flows','/cmd-history','/system-logs']:
            response=page.goto('http://127.0.0.1:5000'+route,wait_until='load')
            assert response.status==200,route
            if route=='/operations':
                page.get_by_role('link',name='Model & data',exact=True).last.click()
                page.get_by_role('heading',name='Offline evaluations').wait_for()
                page.get_by_text('cicids2017 — logistic_regression',exact=True).wait_for()
                assert page.get_by_text('cicids2017 — logistic_regression',exact=True).count()==1
                assert page.get_by_text('unsw-nb15 — random_forest',exact=True).count()==1
                page.get_by_role('link',name='Overview',exact=True).click()
                page.screenshot(path='artifacts/operations-desktop.png',full_page=True)
                page.set_viewport_size({'width':390,'height':844})
                page.screenshot(path='artifacts/operations-mobile.png',full_page=True)
                assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth'), 'mobile overflow'
                page.set_viewport_size({'width':1440,'height':1100})
        browser.close()
    Path('artifacts/browser-check.json').write_text(json.dumps(dict(page_errors=errors,pages=5),indent=2))
    if errors:
        raise AssertionError(errors)
    print('Five browser pages passed; no JavaScript errors; operations responsive at 390px')


if __name__=='__main__': main()
