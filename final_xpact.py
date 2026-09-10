from pathlib import Path

from selenium.webdriver.chrome.options import Options
from selenium import webdriver


def run_wave(driver, url: str, wave_js_path: str) -> dict:
    """
    Run WAVE in the browser and return WAVE statistics together
    with unique findings containing only category and HTML.
    """

    driver.get(url)

    wave_js = Path(wave_js_path).read_text(encoding="utf-8")

    # ---------------------------------------------------------
    # Inject WAVE
    # ---------------------------------------------------------

    driver.execute_async_script(
        """
        const done = arguments[arguments.length - 1];
        const source = arguments[0];

        try {
            const existing = document.getElementById("wavescript");

            if (existing) {
                existing.remove();
            }

            const script = document.createElement("script");
            script.id = "wavescript";
            script.textContent = source;

            (document.head || document.documentElement)
                .appendChild(script);

            done(typeof window.wave !== "undefined");

        } catch (e) {
            done(false);
        }
        """,
        wave_js,
    )

    initialized = driver.execute_script(
        "return typeof window.wave !== 'undefined';"
    )

    if not initialized:
        raise RuntimeError("WAVE failed to initialize")

    # ---------------------------------------------------------
    # Execute WAVE
    # ---------------------------------------------------------

    script = """
    const done = arguments[arguments.length - 1];

    (async () => {
        try {

            if (!window.wave) {
                throw new Error("window.wave is undefined");
            }

            // Initialize WAVE tags.
            window.wave.fn.setupTags();

            // Run the actual WAVE engine.
            await window.wave.engine.run();

            // IMPORTANT:
            // These are WAVE's own results.
            const categories = window.wave.engine.results;
            const statistics = window.wave.engine.statistics;

            // Let WAVE construct its normal structured output.
            window.wave.engine.fn.structureOutput();

            // -------------------------------------------------
            // Helper: resolve XPath
            // -------------------------------------------------

            function getElementFromXPath(xpath) {

                if (!xpath || xpath === "#") {
                    return null;
                }

                try {

                    const result = document.evaluate(
                        xpath,
                        document,
                        null,
                        XPathResult.FIRST_ORDERED_NODE_TYPE,
                        null
                    );

                    return result.singleNodeValue;

                } catch (e) {
                    return null;
                }
            }

            // -------------------------------------------------
            // Extract findings directly from WAVE categories.
            //
            // IMPORTANT:
            // We do NOT calculate category counts here.
            // WAVE statistics remain authoritative.
            // -------------------------------------------------

            const findings = [];

            // Prevent exact duplicate findings.
            const seen = new Set();

            for (
                const [categoryId, category]
                of Object.entries(categories)
            ) {

                if (!category || !category.items) {
                    continue;
                }

                for (
                    const [ruleId, rule]
                    of Object.entries(category.items)
                ) {

                    // WAVE can have different data layouts
                    // depending on the rule.

                    const xpaths = Array.isArray(rule.xpaths)
                        ? rule.xpaths
                        : [];

                    const selectors = Array.isArray(rule.selectors)
                        ? rule.selectors
                        : [];

                    // -------------------------------------------------
                    // Normal WAVE findings
                    // -------------------------------------------------

                    for (let i = 0; i < xpaths.length; i++) {

                        const xpath = xpaths[i] || null;
                        const selector = selectors[i] || null;

                        const element =
                            getElementFromXPath(xpath);

                        let html = null;

                        if (element) {
                            html = element.outerHTML;
                        }

                        // Use the WAVE rule + actual element as identity.
                        //
                        // Do NOT deduplicate using HTML alone because
                        // the same element can legitimately have
                        // different WAVE rules.
                        //

                        let elementIdentity =
                            xpath ||
                            selector ||
                            html ||
                            String(i);

                        const key =
                            categoryId +
                            "|" +
                            ruleId +
                            "|" +
                            elementIdentity;

                        if (seen.has(key)) {
                            continue;
                        }

                        seen.add(key);

                        findings.push({
                            category: categoryId,
                            rule: ruleId,
                            html: html
                        });
                    }

                    // -------------------------------------------------
                    // Some WAVE results may have selectors without
                    // corresponding xpaths.
                    // -------------------------------------------------

                    if (
                        xpaths.length === 0 &&
                        selectors.length > 0
                    ) {

                        for (let i = 0; i < selectors.length; i++) {

                            const selector = selectors[i];

                            let element = null;

                            if (selector) {
                                try {
                                    element =
                                        document.querySelector(
                                            selector
                                        );
                                } catch (e) {
                                    element = null;
                                }
                            }

                            const html =
                                element
                                    ? element.outerHTML
                                    : null;

                            const key =
                                categoryId +
                                "|" +
                                ruleId +
                                "|" +
                                (
                                    selector ||
                                    html ||
                                    String(i)
                                );

                            if (seen.has(key)) {
                                continue;
                            }

                            seen.add(key);

                            findings.push({
                                category: categoryId,
                                rule: ruleId,
                                html: html
                            });
                        }
                    }
                }
            }

            done({
                success: true,

                statistics: statistics,

                categories: categories,

                findings: findings
            });

        } catch (e) {

            done({
                success: false,

                error:
                    e && e.stack
                        ? e.stack
                        : String(e)
            });
        }
    })();
    """

    result = driver.execute_async_script(script)

    if not result["success"]:
        raise RuntimeError(
            f"WAVE execution failed: {result['error']}"
        )

    # ---------------------------------------------------------
    # Final compact response
    # ---------------------------------------------------------

    return {
        "statistics": result["statistics"],

        "details": [
            {
                "category": finding["category"],
                "html": finding["html"]
            }
            for finding in result["findings"]
        ]
    }


# =============================================================
# Selenium
# =============================================================

options = Options()

# options.add_argument("--headless=new")

options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--window-size=1920,1080")

driver = webdriver.Chrome(options=options)


try:

    result = run_wave(
        driver,
        "https://netbeans.apache.org/front/main/index.html",
        r"",
    )

    print(result)

finally:

    driver.quit()