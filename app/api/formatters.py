from app.models.diagnostic import DiagnosticResult, SymptomDiagnosisResult
from app.core.config import settings


def format_diagnostic_response(result: DiagnosticResult) -> list[str]:
    """
    Format diagnostic result into WhatsApp messages (max 1,500 chars each).

    Uses markdown formatting per CLAUDE.md requirements:
    - *bold* for headers
    - • bullets for lists
    - _italic_ for disclaimers

    Args:
        result: DiagnosticResult to format

    Returns:
        List of message strings (split if >1,500 chars)
    """
    max_causes = settings.reply_max_causes
    max_checks = settings.reply_max_checks

    base = f"""*Fault code:* {result.code}
*System:* {result.source}

*What it means:*
{result.description}

*Likely causes:*
{chr(10).join(f"• {c}" for c in result.causes[:max_causes])}

*Recommended action:*
{chr(10).join(f"{i+1}. {c}" for i, c in enumerate(result.checks[:max_checks]))}

_Always confirm with live scanner data before replacing parts._"""

    # Add confidence indicator if available
    if result.confidence >= 0.9:
        confidence_label = "High"
    elif result.confidence >= 0.7:
        confidence_label = "Medium"
    else:
        confidence_label = "Low"

    base += f"\n_Confidence: {confidence_label}_"

    # Split by 1,500 chars if needed
    return _split_message(base, max_length=1500)


def format_symptom_response(result: SymptomDiagnosisResult) -> list[str]:
    """
    Format symptom-based diagnosis into WhatsApp messages.

    Args:
        result: SymptomDiagnosisResult to format

    Returns:
        List of message strings
    """
    max_codes = settings.reply_max_codes
    max_checks = settings.reply_max_checks

    base = "*Diagnosis Summary*\n\n"

    if result.likely_systems:
        base += "*Possible issues detected in:*\n"
        base += ", ".join(result.likely_systems[:5]) + "\n\n"

    if result.probable_codes:
        base += "*Common codes:*\n"
        base += ", ".join(result.probable_codes[:max_codes]) + "\n\n"

    if result.recommended_checks:
        base += "*Recommended checks:*\n"
        base += "\n".join(
            f"• {c}" for c in result.recommended_checks[:max_checks]
        ) + "\n\n"

    base += "Would you like to scan for codes?\n"
    base += "_Symptom-based guidance. Confirm with a scan and inspection._"

    return _split_message(base, max_length=1500)


def format_error_response(error_msg: str) -> list[str]:
    """
    Format error message for WhatsApp.

    Args:
        error_msg: Error message string

    Returns:
        List with single message
    """
    return [error_msg]


def _split_message(text: str, max_length: int = 1500) -> list[str]:
    """
    Split message into chunks respecting line breaks.

    Args:
        text: Message text
        max_length: Maximum characters per message

    Returns:
        List of message chunks with "1/N" prefixes if split
    """
    if len(text) <= max_length:
        return [text]

    # Split by lines and group into chunks
    lines = text.split("\n")
    chunks = []
    current_chunk = []
    current_length = 0

    for line in lines:
        line_length = len(line) + 1  # +1 for newline

        if current_length + line_length > max_length and current_chunk:
            # Save current chunk and start new one
            chunks.append("\n".join(current_chunk))
            current_chunk = [line]
            current_length = line_length
        else:
            current_chunk.append(line)
            current_length += line_length

    # Add final chunk
    if current_chunk:
        chunks.append("\n".join(current_chunk))

    # Add "1/N" prefixes if multiple chunks
    if len(chunks) > 1:
        return [
            f"{i+1}/{len(chunks)}\n{chunk}"
            for i, chunk in enumerate(chunks)
        ]

    return chunks
