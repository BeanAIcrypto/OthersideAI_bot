
MESSAGES = {
    "start_error": "An error occurred while executing the /start command.",

    "handle_language_choice_first_message": {
        "en": "Greetings :) You are free to explore the Otherside meta universe and ask me any questions you want."
    },

    "handle_export_logs_file_not_found": "Logs file not found.",
    "handle_export_logs_error": "An error occurred while exporting logs.",

    "link_handler": {
        "en": "Link not found"
    },
    "link_handler_await": {
        "en": "Please wait, it may take some time"
    },
    "link_handler_error_data": {
        "en": "This one from the link could not be retrieved"
    },

    "document_handler_error": {
        "en": "I couldn't retrieve the data. Try another format"
    },
    "document_handler_not_found": {
        "en": "This format is not supported"
    },

    "all_updates_handler": {
        "en": "Oops 🙈 I can't process this file format yet. Please write your question, send a voice message, or try another file format :)"
    },

    "check_subscribed_handler": {
        "en": "Thanks for subscribing!"
    },
    "check_subscribed_handler_not_found": {
        "en": "You haven't subscribed to the channel yet"
    },
    "check_subscribed_handler_error": {
        "en": "You haven't subscribed to the channel yet"
    },

    "process_callback_rating": {
        "en": "Thank you for your rating! You may ask the following question"
    },
    "process_callback_rating_error": {
        "en": "There was an error in processing your assessment"
    },

    "handle_empty_transcription": {
        "en": "Failed to recognize the voice message. Please try again."
    },
    "you_tube_link_processing_error_download": {
        "en": "Failed to upload video"
    },
    "you_tube_link_processing_error": {
        "en": "Error in video processing"
    },

    "count_vois_tokens": {
        "en": "Your question is over the limit, ask another or try asking tomorrow"
    },
    "get_user_limit": {
        "en": "Sorry, message limit has been exceeded for today. Check back with us tomorrow :)"
    },

    "process_user_message": {
        "en": "Your reply is being processed ⏳"
    },

    'send_reminder_24h': {
        'en': "Hey! I noticed you haven't logged in for a while 🤔\n\n"
              "The metaverse won’t wait! "
              "It's time to dive back in — I’ve prepared a few exciting updates for you 💡 Check them out!"
    },
    'send_reminder_72h': {
        'en': "You still haven't come back, and I've already found some cool news from the metaverse!\n\n"
              "If you're curious about what's going on in virtual worlds and the opportunities they bring, "
              "hit the command — it's going to be exciting 🚀"
    },
    'send_reminder_168h': {
        'en': "It's been a whole week since we last chatted!\n\n"
              "I'm sure you have some questions about the metaverse. "
              "Let’s dive in — I’ll help you explore everything from platforms to the latest trends. "
              "Just press the button below to begin!"
    },

    'send_subscription_reminder_24': {
        'en': "Want to stay updated with the latest news from the Otherside metaverse? \n"
              "Subscribe to our channel! You'll find not only useful tips but also exclusive materials.\n"
              "Don't miss out 🚀:\n "
    },

    'strategy_investment': {
        'en': "Tell us about crypto investment strategies"
    },
    'improve_portfolio': {
        'en': "How do you improve your portfolio?"
    },
    "donate_error": {
        "en": "An error occurred while creating the payment link. Please try again later."
    },

    "rating_request": {
        "en": "Please rate the received answer:"
    },
    "donate": {
        "en": "To make a donation to the project, you can make a donation to our wallet\\.\n"
              "Networks: BNB, ARB, OP, ERC20\\.\n"
              "```0x1D99EdC1431f27cF26FF8a464A814Ba2Bb757602```\n"
    },
    "unexpected_error": {
        "en": "Error: An unexpected error occurred while processing the request. Please try again or contact support."
    },
}

MESSAGES_ERROR = {
    "processing_error": {
        "en": "An error occurred while processing your request. Please try again later."
    },
    "token_limit_exceeded": {
        "en": "You have exceeded your token limit. Please wait or upgrade your plan."
    },
    "unexpected_error": {
        "en": "An unexpected error occurred. Please contact support if the issue persists."
    },
    "error_response": {
        "en": "An error occurred while processing your request. Please try again later."
    },
    "markdown_error": {
        "en": "An error occurred while formatting the response."
    },
    "limit_exceeded": {
        "en": "Your question exceeds the daily token limit. Please try another question or wait until tomorrow."
    },
    "transcription_error": {
        "en": "An error occurred while processing the audio. Please try again."
    },
    "empty_transcription": {
        "en": "Could not recognize text from audio. Please try recording your message again."
    },
    "you_tube_link_processing_error_download": {
        "en": "Failed to download the video. Please check the link and try again."
    },
    "you_tube_link_processing_error_split": {
        "en": "Failed to split the audio file into parts. Please try another video."
    },
    "you_tube_link_processing_error_transcription": {
        "en": "An error occurred during audio transcription. Please try again."
    },
    "count_vois_tokens": {
        "en": "Your request exceeds the token limit. Please try a different request."
    },
    "general_processing_error": {
        "en": "An error occurred while processing the video. Please try again."
    },
    "dynamic_page_timeout": {
        "en": "Timeout while loading the dynamic page. Please check the website availability and try again."
    },
    "dynamic_page_access_denied": {
        "en": "The website is protected and does not allow automated access. Please try opening it manually."
    },
    "dynamic_page_error": {
        "en": "Error while processing the dynamic page. Please try again later."
    },
    "static_page_error": {
        "en": "Error while processing the static page. Please check the link and try again."
    },
    "link_processing_error": {
        "en": "Error while processing the link. Please check its correctness."
    },
    "unsupported_format": {
        "en": "The file contains an unsupported format."
    },
    "extraction_error": {
        "en": "An error occurred while extracting text from the file."
    },
    "archive_extraction_error": {
        "en": "An error occurred while processing the archive."
    },
    "mhtml_extraction_error": {
        "en": "Failed to extract text from the MHTML file."
    },
    "document_handler_error_type_document": {
        "en": "Supported formats:\n"
              "📄 Documents: PDF (.pdf), Word (.docx) (Convert .doc to .docx)\n"
              "📊 Spreadsheets: Excel (.xlsx) (Convert .xls to .xlsx)\n"
              "📽 Presentations: PowerPoint (.pptx) (Convert .ppt to .pptx)\n"
              "📦 Archives: ZIP (.zip), 7Z (.7z) (Convert .rar to .zip)\n"
              "📝 Markdown: .md\n\n"
              "If your file is not supported, please convert it before sending."
    },
    "document_handler_error_none_document": {
        "en": "Failed to extract data. Try a different format or check the document's content."
    }
}

MESSAGES_ERROR_YOU_TUBE_LINK_PROCESSING = {
    "no_transcript": {
        "en": "Unfortunately, this video has no available subtitles."
    },
    "transcripts_disabled": {
        "en": "Subtitles are disabled for this video."
    },
    "connection_error": {
        "en": "Connection error. Please try again later."
    },
    "timeout_error": {
        "en": "Timeout error. Please try again."
    },
    "file_not_found": {
        "en": "Error: File not found."
    },
    "permission_error": {
        "en": "Permission error. Please check your settings."
    },
    "import_error": {
        "en": "Import error. Please install the necessary package using `pip install youtube-transcript-api`."
    },
    "value_error": {
        "en": "Value error. Please check the input data."
    },
    "type_error": {
        "en": "Type error. Check argument types."
    },
    "unknown_error": {
        "en": "An unknown error occurred. Please try again later."
    }
}
