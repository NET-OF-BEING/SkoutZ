"""Scroll helpers for SKOUT's internal Discover page layout."""


SCROLL_DISCOVER_PAGE_SCRIPT = """
const amount = arguments[0] || Math.max(700, Math.floor(window.innerHeight * 0.85));
const selectors = 'main, [role="main"], section, div';
const rawCandidates = [
    document.scrollingElement,
    document.documentElement,
    document.body,
    ...document.querySelectorAll(selectors)
].filter(Boolean);
const seen = new Set();
const scrollableCandidates = [];

for (const element of rawCandidates) {
    if (seen.has(element)) continue;
    seen.add(element);

    const style = window.getComputedStyle(element);
    const rect = element.getBoundingClientRect();
    const maxScroll = element.scrollHeight - element.clientHeight;
    const canScroll = maxScroll > 20;
    const isVisible = rect.width > 100 && rect.height > 100;
    const allowsScroll = /(auto|scroll|overlay|visible)/.test(style.overflowY);

    if (!canScroll || !isVisible || !allowsScroll) continue;

    scrollableCandidates.push({
        element,
        maxScroll,
        before: element.scrollTop,
        area: rect.width * rect.height,
        tag: element.tagName,
        className: String(element.className || '').slice(0, 80)
    });
}

scrollableCandidates.sort((left, right) => {
    if (right.maxScroll !== left.maxScroll) return right.maxScroll - left.maxScroll;
    return right.area - left.area;
});

for (const candidate of scrollableCandidates) {
    const {element, before, maxScroll} = candidate;
    element.scrollTop = Math.min(before + amount, maxScroll);
    element.dispatchEvent(new Event('scroll', {bubbles: true}));
    window.dispatchEvent(new Event('scroll'));

    if (element.scrollTop !== before) {
        return {
            scrolled: true,
            target: candidate.tag + (candidate.className ? '.' + candidate.className : ''),
            before,
            after: element.scrollTop,
            maxScroll
        };
    }
}

const beforeWindow = window.scrollY;
window.scrollBy({top: amount, left: 0, behavior: 'instant'});
window.dispatchEvent(new Event('scroll'));

return {
    scrolled: window.scrollY !== beforeWindow,
    target: 'window',
    before: beforeWindow,
    after: window.scrollY,
    maxScroll: Math.max(
        document.documentElement.scrollHeight,
        document.body ? document.body.scrollHeight : 0
    ) - window.innerHeight
};
"""


def scroll_discover_page(driver, wait_after_scroll, pixels=None):
    """
    Scroll the SKOUT Discover view, including internal scroll containers.

    The desktop layout often keeps the document fixed and scrolls a central
    content container, so a body-only window.scrollTo call can be a no-op.
    """
    result = driver.execute_script(SCROLL_DISCOVER_PAGE_SCRIPT, pixels)
    wait_after_scroll()
    return result or {"scrolled": False, "target": "unknown"}
