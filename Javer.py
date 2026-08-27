from pathlib import Path

from selenium.webdriver.chrome.options import Options
from selenium import webdriver


def run_wave(driver, url: str, wave_js_path: str) -> dict:
    """
    Load a URL, inject WAVE into the page context, execute WAVE,
    and return WAVE results, documentation, and element HTML.
    """

    driver.get(url)

    wave_js = Path(wave_js_path).read_text(encoding="utf-8")

    # Inject WAVE into the page context.
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

            if (window.wave) {
                done(true);
            } else {
                done(false);
            }

        } catch (e) {
            done(false);
        }
        """,
        wave_js,
    )

    # Verify WAVE initialized.
    initialized = driver.execute_script(
        "return typeof window.wave !== 'undefined';"
    )

    if not initialized:
        raise RuntimeError(
            "WAVE failed to initialize in page context"
        )

    script = """
    const done = arguments[arguments.length - 1];

    (async () => {
        try {

            if (!window.wave) {
                throw new Error("window.wave is undefined");
            }

            // Initialize WAVE.
            window.wave.fn.setupTags();

            window.wave.results = {};
            window.wave.results.statistics = {};

            // Execute all WAVE rules.
            await window.wave.engine.run();

            window.wave.results.categories =
                window.wave.engine.results;

            window.wave.results.statistics =
                window.wave.engine.statistics;

            // Build WAVE structured output.
            window.wave.engine.fn.structureOutput();

            // WAVE documentation.
            const docs = {};

            if (
                window.wave.engine.icons &&
                window.wave.engine.icons.docs
            ) {
                for (
                    const [name, doc]
                    of Object.entries(
                        window.wave.engine.icons.docs
                    )
                ) {
                    docs[name] = doc;
                }
            }

            // --------------------------------------------------
            // Extract individual findings + actual HTML
            // --------------------------------------------------

            const findings = [];

            for (
                const [categoryId, category]
                of Object.entries(
                    window.wave.results.categories
                )
            ) {

                if (!category || !category.items) {
                    continue;
                }

                for (
                    const [ruleId, rule]
                    of Object.entries(category.items)
                ) {

                    const xpaths = rule.xpaths || [];
                    const hidden = rule.hidden || [];
                    const text = rule.text || [];
                    const selectors = rule.selectors || [];

                    for (
                        let i = 0;
                        i < xpaths.length;
                        i++
                    ) {

                        const xpath = xpaths[i];

                        let element = null;

                        if (xpath && xpath !== "#") {
                            try {
                                const result =
                                    document.evaluate(
                                        xpath,
                                        document,
                                        null,
                                        XPathResult
                                            .FIRST_ORDERED_NODE_TYPE,
                                        null
                                    );

                                element =
                                    result.singleNodeValue;
                            } catch (e) {
                                element = null;
                            }
                        }

                        findings.push({
                            category: categoryId,

                            rule: ruleId,

                            description:
                                rule.description || null,

                            xpath: xpath || null,

                            selector:
                                selectors[i] || null,

                            hidden:
                                hidden[i] || false,

                            text:
                                text[i] || null,

                            html:
                                element
                                    ? element.outerHTML
                                    : null
                        });
                    }
                }
            }

            done({
                success: true,

                url: window.location.href,

                title: document.title,

                statistics:
                    window.wave.results.statistics,

                categories:
                    window.wave.results.categories,

                findings: findings,

                documentation: docs
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

    return result


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

    # -----------------------------------------------------
    # Categories / rule counts
    # -----------------------------------------------------

    categories = result["categories"]

    for category_id, category in categories.items():

        print(
            f"\n=== {category['description']} ==="
        )

        for rule_id, rule in category["items"].items():

            print(
                rule_id,
                "|",
                rule["description"],
                "|",
                rule["count"],
            )

    # -----------------------------------------------------
    # Individual findings + HTML
    # -----------------------------------------------------

    print("\n\n========== FINDINGS ==========")

    for finding in result["findings"]:

        #print("\nRule:", finding["rule"])
        print("Category:", finding["category"])
        #print("Description:", finding["description"])
        #print("XPath:", finding["xpath"])
        print("HTML:", finding["html"])

finally:

    driver.quit()
