from selenium.webdriver.common.by import By


class AccessibilityInfoTool:

    def __init__(self, driver):
        self.driver = driver

    def run(self, selector: str) -> dict:
        elements = self.driver.find_elements(
            By.CSS_SELECTOR,
            selector
        )

        if not elements:
            return {
                "found": False,
                "selector": selector,
                "reason": "No element matched the selector."
            }

        if len(elements) > 1:
            return {
                "found": False,
                "selector": selector,
                "reason": "Selector matched multiple elements.",
                "match_count": len(elements)
            }

        element = elements[0]

        info = self.driver.execute_script("""
            const element = arguments[0];

            const ariaAttributes = [
                "aria-label",
                "aria-labelledby",
                "aria-describedby",
                "aria-hidden",
                "aria-expanded",
                "aria-pressed",
                "aria-checked",
                "aria-disabled",
                "aria-selected",
                "aria-controls"
            ];

            const aria = {};

            for (const attr of ariaAttributes) {
                const value = element.getAttribute(attr);

                if (value !== null) {
                    aria[attr] = value;
                }
            }

            return {
                role: element.getAttribute("role"),

                aria: aria,

                label: element.getAttribute("label"),

                title: element.getAttribute("title"),

                name: element.getAttribute("name"),

                type: element.getAttribute("type")
            };
        """, element)

        return {
            "found": True,
            "selector": selector,
            **info
        }