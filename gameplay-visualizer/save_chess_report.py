"""
Custom Save File Component for HTML Chess Reports
Extends the Langflow Save File component to handle HTML files
"""

import json
from collections.abc import AsyncIterator, Iterator
from pathlib import Path
from datetime import datetime

import orjson
import pandas as pd
from fastapi import UploadFile
from fastapi.encoders import jsonable_encoder

from langflow.api.v2.files import upload_user_file
from langflow.custom import Component
from langflow.io import DropdownInput, HandleInput, StrInput
from langflow.schema import Data, DataFrame, Message
from langflow.services.auth.utils import create_user_longterm_token
from langflow.services.database.models.user.crud import get_user_by_id
from langflow.services.deps import get_session, get_settings_service, get_storage_service
from langflow.template.field.base import Output


class CustomSaveToFileComponent(Component):
    display_name = "Save Chess Report"
    description = "Save chess analysis HTML report to a local file with automatic naming."
    documentation: str = "https://docs.langflow.org/components-processing#save-file"
    icon = "save"
    name = "SaveChessReport"

    # File format options for different types
    DATA_FORMAT_CHOICES = ["csv", "excel", "json", "markdown"]
    MESSAGE_FORMAT_CHOICES = ["txt", "json", "markdown", "html"]

    inputs = [
        HandleInput(
            name="html_content",
            display_name="HTML Content",
            info="The HTML content to save (from Chess Visualizer).",
            input_types=["Message"],
            required=True,
        ),
        StrInput(
            name="save_directory",
            display_name="Save Directory",
            info="Directory to save the file (default: current directory).",
            value="./chess_reports",
            advanced=True,
        ),
    ]

    outputs = [Output(display_name="File Path", name="result", method="save_chess_report")]

    async def save_chess_report(self) -> Message:
        """Save the chess report HTML to a file with automatic naming."""
        # Validate inputs
        if not self.html_content:
            msg = "HTML content must be provided."
            raise ValueError(msg)

        # Extract HTML content from Message
        html_content = ""
        if isinstance(self.html_content.text, AsyncIterator):
            async for item in self.html_content.text:
                html_content += str(item)
        elif isinstance(self.html_content.text, Iterator):
            html_content = "".join(str(item) for item in self.html_content.text)
        else:
            html_content = str(self.html_content.text)

        # Extract username from HTML content (look for username in the HTML)
        username = "unknown_user"
        try:
            # Look for username in the HTML title or content
            import re
            
            # Try multiple patterns to find username
            patterns = [
                r'<h2>([^<]+)</h2>',  # Username in h2 tag (most likely)
                r'Chess Style Analysis: ([^<]+)',  # In title text
                r'Report - ([^<]+)</title>',  # In page title
                r'chess_analysis_([^_]+)_',  # In existing filename patterns
                r'Username: ([^<\s]+)',  # Direct username label
                r'username["\s:]*["\s]*([a-zA-Z0-9_]+)',  # General username pattern
            ]
            
            for pattern in patterns:
                match = re.search(pattern, html_content, re.IGNORECASE)
                if match:
                    extracted = match.group(1).strip()
                    # Make sure it's a valid username (alphanumeric + underscore only)
                    if re.match(r'^[a-zA-Z0-9_]+$', extracted) and len(extracted) > 2:
                        username = extracted
                        break
            
            print(f"Extracted username: {username}")
            
        except Exception as e:
            print(f"Could not extract username from HTML: {e}")
            username = "unknown_user"

        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"chess_analysis_{username}_{timestamp}.html"
        
        # Prepare file path
        save_dir = Path(self.save_directory).expanduser()
        save_dir.mkdir(parents=True, exist_ok=True)
        file_path = save_dir / filename

        try:
            # Save HTML file
            file_path.write_text(html_content, encoding='utf-8')
            
            # Upload the saved file
            await self._upload_file(file_path)

            # Return confirmation
            absolute_path = file_path.absolute()
            confirmation_msg = f"""✅ Chess Analysis Report Saved Successfully!

📁 File Details:
• Location: {absolute_path}
• Username: {username}
• Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
• File Size: {file_path.stat().st_size / 1024:.1f} KB

🌐 To view your report:
1. Open the file in any web browser
2. All charts are embedded (no internet required)
3. File is self-contained and portable

The report includes comprehensive opening analysis and player profile visualizations."""

            return Message(text=confirmation_msg)

        except Exception as e:
            error_msg = f"❌ Error saving chess report: {str(e)}"
            raise ValueError(error_msg)

    async def _upload_file(self, file_path: Path) -> None:
        """Upload the saved file using the upload_user_file service."""
        if not file_path.exists():
            msg = f"File not found: {file_path}"
            raise FileNotFoundError(msg)

        try:
            with file_path.open("rb") as f:
                async for db in get_session():
                    user_id, _ = await create_user_longterm_token(db)
                    current_user = await get_user_by_id(db, user_id)

                    await upload_user_file(
                        file=UploadFile(filename=file_path.name, file=f, size=file_path.stat().st_size),
                        session=db,
                        current_user=current_user,
                        storage_service=get_storage_service(),
                        settings_service=get_settings_service(),
                    )
        except Exception as e:
            # Don't fail the entire operation if upload fails
            print(f"Warning: Could not upload file to Langflow storage: {e}")
            pass


# Alternative: Modify the existing Save File component to handle HTML better
class EnhancedSaveToFileComponent(Component):
    display_name = "Enhanced Save File"
    description = "Enhanced save file component with better HTML support and auto-naming."
    documentation: str = "https://docs.langflow.org/components-processing#save-file"
    icon = "save"
    name = "EnhancedSaveToFile"

    # Enhanced file format options
    DATA_FORMAT_CHOICES = ["csv", "excel", "json", "markdown"]
    MESSAGE_FORMAT_CHOICES = ["txt", "json", "markdown", "html"]

    inputs = [
        HandleInput(
            name="input",
            display_name="Input",
            info="The input to save.",
            dynamic=True,
            input_types=["Data", "DataFrame", "Message"],
            required=True,
        ),
        StrInput(
            name="file_name",
            display_name="File Name",
            info="Name file will be saved as. For chess reports, use format: username_YYYYMMDD_HHMMSS",
            required=True,
        ),
        DropdownInput(
            name="file_format",
            display_name="File Format",
            options=list(dict.fromkeys(DATA_FORMAT_CHOICES + MESSAGE_FORMAT_CHOICES)),
            info="Select the file format. Use 'html' for chess visualization reports.",
            value="html",
            advanced=True,
        ),
        StrInput(
            name="save_directory",
            display_name="Save Directory",
            info="Directory to save the file (default: current directory).",
            value="./chess_reports",
            advanced=True,
        ),
    ]

    outputs = [Output(display_name="File Path", name="result", method="save_to_file")]

    async def save_to_file(self) -> Message:
        """Enhanced save to file with better HTML handling."""
        # Validate inputs
        if not self.file_name:
            msg = "File name must be provided."
            raise ValueError(msg)
        if not self._get_input_type():
            msg = "Input type is not set."
            raise ValueError(msg)

        # Validate file format based on input type
        file_format = self.file_format or self._get_default_format()
        allowed_formats = (
            self.MESSAGE_FORMAT_CHOICES if self._get_input_type() == "Message" else self.DATA_FORMAT_CHOICES
        )
        if file_format not in allowed_formats:
            msg = f"Invalid file format '{file_format}' for {self._get_input_type()}. Allowed: {allowed_formats}"
            raise ValueError(msg)

        # Prepare file path with directory
        save_dir = Path(self.save_directory).expanduser()
        save_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = save_dir / self.file_name
        file_path = self._adjust_file_path_with_format(file_path, file_format)

        # Save the input to file based on type
        if self._get_input_type() == "DataFrame":
            confirmation = self._save_dataframe(self.input, file_path, file_format)
        elif self._get_input_type() == "Data":
            confirmation = self._save_data(self.input, file_path, file_format)
        elif self._get_input_type() == "Message":
            confirmation = await self._save_message(self.input, file_path, file_format)
        else:
            msg = f"Unsupported input type: {self._get_input_type()}"
            raise ValueError(msg)

        # Upload the saved file
        await self._upload_file(file_path)

        # Return enhanced confirmation with file details
        final_path = file_path.absolute()
        file_size = file_path.stat().st_size / 1024  # KB
        
        enhanced_confirmation = f"""✅ {confirmation}

📁 File Information:
• Location: {final_path}
• Format: {file_format.upper()}
• Size: {file_size:.1f} KB
• Created: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

{self._get_format_specific_info(file_format)}"""

        return Message(text=enhanced_confirmation)

    def _get_format_specific_info(self, file_format: str) -> str:
        """Get format-specific information for the user."""
        if file_format == "html":
            return """🌐 HTML Report Details:
• Open in any web browser to view
• All images are embedded (no external dependencies)
• File is portable and self-contained
• Optimized for chess analysis visualization"""
        elif file_format == "json":
            return "📄 JSON format: Machine-readable structured data"
        elif file_format == "csv":
            return "📊 CSV format: Compatible with Excel and data analysis tools"
        elif file_format == "markdown":
            return "📝 Markdown format: Human-readable with formatting"
        else:
            return ""

    def _get_input_type(self) -> str:
        """Determine the input type based on the provided input."""
        if type(self.input) is DataFrame:
            return "DataFrame"
        if type(self.input) is Message:
            return "Message"
        if type(self.input) is Data:
            return "Data"
        msg = f"Unsupported input type: {type(self.input)}"
        raise ValueError(msg)

    def _get_default_format(self) -> str:
        """Return the default file format based on input type."""
        if self._get_input_type() == "DataFrame":
            return "csv"
        if self._get_input_type() == "Data":
            return "json"
        if self._get_input_type() == "Message":
            return "html"  # Default to HTML for Message type
        return "json"

    def _adjust_file_path_with_format(self, path: Path, fmt: str) -> Path:
        """Adjust the file path to include the correct extension."""
        file_extension = path.suffix.lower().lstrip(".")
        if fmt == "excel":
            return Path(f"{path}.xlsx").expanduser() if file_extension not in ["xlsx", "xls"] else path
        return Path(f"{path}.{fmt}").expanduser() if file_extension != fmt else path

    async def _upload_file(self, file_path: Path) -> None:
        """Upload the saved file using the upload_user_file service."""
        if not file_path.exists():
            msg = f"File not found: {file_path}"
            raise FileNotFoundError(msg)

        try:
            with file_path.open("rb") as f:
                async for db in get_session():
                    user_id, _ = await create_user_longterm_token(db)
                    current_user = await get_user_by_id(db, user_id)

                    await upload_user_file(
                        file=UploadFile(filename=file_path.name, file=f, size=file_path.stat().st_size),
                        session=db,
                        current_user=current_user,
                        storage_service=get_storage_service(),
                        settings_service=get_settings_service(),
                    )
        except Exception as e:
            # Don't fail if upload fails
            print(f"Warning: Could not upload to Langflow storage: {e}")

    def _save_dataframe(self, dataframe: DataFrame, path: Path, fmt: str) -> str:
        """Save a DataFrame to the specified file format."""
        if fmt == "csv":
            dataframe.to_csv(path, index=False)
        elif fmt == "excel":
            dataframe.to_excel(path, index=False, engine="openpyxl")
        elif fmt == "json":
            dataframe.to_json(path, orient="records", indent=2)
        elif fmt == "markdown":
            path.write_text(dataframe.to_markdown(index=False), encoding="utf-8")
        else:
            msg = f"Unsupported DataFrame format: {fmt}"
            raise ValueError(msg)
        return f"DataFrame saved successfully"

    def _save_data(self, data: Data, path: Path, fmt: str) -> str:
        """Save a Data object to the specified file format."""
        if fmt == "csv":
            pd.DataFrame(data.data).to_csv(path, index=False)
        elif fmt == "excel":
            pd.DataFrame(data.data).to_excel(path, index=False, engine="openpyxl")
        elif fmt == "json":
            path.write_text(
                orjson.dumps(jsonable_encoder(data.data), option=orjson.OPT_INDENT_2).decode("utf-8"), encoding="utf-8"
            )
        elif fmt == "markdown":
            path.write_text(pd.DataFrame(data.data).to_markdown(index=False), encoding="utf-8")
        else:
            msg = f"Unsupported Data format: {fmt}"
            raise ValueError(msg)
        return f"Data saved successfully"

    async def _save_message(self, message: Message, path: Path, fmt: str) -> str:
        """Enhanced save message with HTML support."""
        content = ""
        if message.text is None:
            content = ""
        elif isinstance(message.text, AsyncIterator):
            async for item in message.text:
                content += str(item)
        elif isinstance(message.text, Iterator):
            content = "".join(str(item) for item in message.text)
        else:
            content = str(message.text)

        if fmt == "txt":
            path.write_text(content, encoding="utf-8")
        elif fmt == "json":
            path.write_text(json.dumps({"message": content}, indent=2), encoding="utf-8")
        elif fmt == "markdown":
            path.write_text(f"**Message:**\n\n{content}", encoding="utf-8")
        elif fmt == "html":
            # Enhanced HTML saving with proper DOCTYPE if missing
            if not content.strip().startswith("<!DOCTYPE") and not content.strip().startswith("<html"):
                content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Langflow Output</title>
</head>
<body>
{content}
</body>
</html>"""
            path.write_text(content, encoding="utf-8")
        else:
            msg = f"Unsupported Message format: {fmt}"
            raise ValueError(msg)
        return f"Message saved successfully"
