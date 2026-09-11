"""Reliable SKOUT message draft entry helpers."""


class MessageDraftError(RuntimeError):
    """Raised when SKOUT clears or changes the prepared draft."""


FOCUS_TEXTAREA_SCRIPT = """
arguments[0].scrollIntoView({behavior: 'instant', block: 'center'});
arguments[0].focus();
"""

READ_TEXTAREA_VALUE_SCRIPT = "return arguments[0].value;"

SET_NATIVE_TEXTAREA_VALUE_SCRIPT = """
const element = arguments[0];
const value = arguments[1];
const descriptor = Object.getOwnPropertyDescriptor(
    window.HTMLTextAreaElement.prototype,
    'value'
);
descriptor.set.call(element, value);
element.dispatchEvent(new InputEvent('input', {
    bubbles: true,
    cancelable: true,
    inputType: value ? 'insertText' : 'deleteContentBackward',
    data: value
}));
element.dispatchEvent(new Event('change', { bubbles: true }));
element.focus();
return element.value;
"""


def read_message_value(driver, textarea):
    """Return the browser-visible value for a textarea."""
    return driver.execute_script(READ_TEXTAREA_VALUE_SCRIPT, textarea)


def focus_message_box(driver, textarea):
    """Move focus into the textarea before using browser-level text insertion."""
    driver.execute_script(FOCUS_TEXTAREA_SCRIPT, textarea)
    try:
        textarea.click()
    except Exception:
        pass


def _set_native_value(driver, textarea, value):
    return driver.execute_script(SET_NATIVE_TEXTAREA_VALUE_SCRIPT, textarea, value)


def _try_browser_insert_text(driver, textarea, message):
    _set_native_value(driver, textarea, "")
    focus_message_box(driver, textarea)
    driver.execute_cdp_cmd("Input.insertText", {"text": message})


def _try_native_input_event(driver, textarea, message):
    focus_message_box(driver, textarea)
    _set_native_value(driver, textarea, message)


def _try_webdriver_keys(driver, textarea, message):
    focus_message_box(driver, textarea)
    textarea.clear()
    textarea.send_keys(message)


def _is_stable_message(driver, textarea, message, wait_after_write):
    wait_after_write()
    entered_message = read_message_value(driver, textarea)
    if entered_message != message:
        return False, entered_message

    wait_after_write()
    entered_message = read_message_value(driver, textarea)
    return entered_message == message, entered_message


def prepare_message_draft(driver, textarea, message, wait_after_write, attempts=3):
    """
    Put a message into a SKOUT textarea and verify the site keeps it there.

    SKOUT uses a controlled textarea in some dialogs. Plain JavaScript assignment
    can briefly show the text, then React state restores an empty value. The
    first strategy uses Chrome's browser-level text insertion; the fallbacks are
    kept for older dialogs and Selenium environments without CDP support.
    """
    strategies = (
        _try_browser_insert_text,
        _try_native_input_event,
        _try_webdriver_keys,
    )
    last_value = ""
    last_error = None

    for _attempt in range(attempts):
        for strategy in strategies:
            try:
                strategy(driver, textarea, message)
                stable, last_value = _is_stable_message(
                    driver,
                    textarea,
                    message,
                    wait_after_write,
                )
                if stable:
                    return message
            except Exception as exc:
                last_error = f"{type(exc).__name__}: {exc}"

    visible_length = 0 if not isinstance(last_value, str) else len(last_value)
    detail = f"Message text verification failed ({visible_length}/{len(message)} characters)"
    if last_error:
        detail = f"{detail}; last input method error: {last_error}"
    raise MessageDraftError(detail)
