from pathlib import Path

from selenium.webdriver.chrome.options import Options
from selenium import webdriver


def run_wave(driver, url: str, wave_js_path: str) -> dict:
    """
    Load a URL, inject WAVE, execute WAVE rules, and return
    WAVE statistics plus unique findings containing category
    and related HTML.
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
    # Execute WAVE and extract findings
    # ---------------------------------------------------------

    script = """
    const done = arguments[arguments.length - 1];

    (async () => {
        try {

            if (!window.wave) {
                throw new Error("window.wave is undefined");
            }

            // Initialize WAVE.
            window.wave.fn.setupTags();

            // Run WAVE.
            await window.wave.engine.run();

            // WAVE's own results and statistics.
            const categories = window.wave.engine.results;
            const statistics = window.wave.engine.statistics;

            // -------------------------------------------------
            // Build unique findings
            // -------------------------------------------------

            const findings = [];
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

                    const xpaths = Array.isArray(rule.xpaths)
                        ? rule.xpaths
                        : [];

                    const selectors = Array.isArray(rule.selectors)
                        ? rule.selectors
                        : [];

                    for (let i = 0; i < xpaths.length; i++) {

                        const xpath = xpaths[i] || null;
                        const selector = selectors[i] || null;

                        let element = null;

                        // -----------------------------------------
                        // Resolve XPath
                        // -----------------------------------------

                        if (xpath && xpath !== "#") {
                            try {

                                const result = document.evaluate(
                                    xpath,
                                    document,
                                    null,
                                    XPathResult.FIRST_ORDERED_NODE_TYPE,
                                    null
                                );

                                element = result.singleNodeValue;

                            } catch (e) {
                                element = null;
                            }
                        }

                        // -----------------------------------------
                        // Create a stable element identity.
                        //
                        // Prefer the actual DOM element when
                        // available. Otherwise fall back to XPath.
                        // -----------------------------------------

                        let elementKey = xpath || selector || String(i);

                        if (element) {
                            elementKey =
                                element.outerHTML +
                                "|" +
                                (element.id || "") +
                                "|" +
                                (element.getAttribute("name") || "");
                        }

                        // -----------------------------------------
                        // A finding is unique by:
                        //
                        // category + rule + element
                        //
                        // This prevents the same WAVE finding from
                        // appearing multiple times.
                        // -----------------------------------------

                        const key =
                            categoryId +
                            "|" +
                            ruleId +
                            "|" +
                            elementKey;

                        if (seen.has(key)) {
                            continue;
                        }

                        seen.add(key);

                        findings.push({
                            category: categoryId,
                            rule: ruleId,
                            html: element
                                ? element.outerHTML
                                : null
                        });
                    }
                }
            }

            done({
                success: true,
                statistics: statistics,
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
    # Compact Python result
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


# ---------------------------------------------------------
# Selenium
# ---------------------------------------------------------

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