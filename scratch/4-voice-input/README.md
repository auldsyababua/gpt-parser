# Voice Input Support for Telegram Bot

## Overview
Add voice message support to the Telegram bot, allowing field workers to create tasks hands-free using speech-to-text.

## Status: READY FOR IMPLEMENTATION

### Prerequisites
- Telegram bot working with text input
- OpenAI API key (for Whisper API)
- Task parsing pipeline functional

### 🎯 Target Features

1. **Voice Message Handling**
   - Receive voice messages in Telegram
   - Download and process audio files
   - Support for common audio formats (OGG, MP3)
   - Handle long voice messages (>1 minute)

2. **Speech-to-Text Conversion**
   - Use OpenAI Whisper API for transcription
   - Support multiple languages (English, Spanish)
   - Handle background noise and accents
   - Show transcription confidence

3. **Confirmation Flow**
   - Show transcribed text to user
   - Allow editing before parsing
   - Inline buttons for confirm/retry/cancel
   - Preserve original audio for reference

4. **Error Handling**
   - Network timeout handling
   - Audio quality warnings
   - Fallback to text input
   - Retry mechanism for failed transcriptions

### 💁 User Experience Flow

```
User: 🎤 [Voice message: "Tell Joel to check the generator oil at Site B tomorrow morning"]

Bot: 🎯 Transcribing your voice message...

Bot: 🔍 I heard: "Tell Joel to check the generator oil at Site B tomorrow morning"
     
     Is this correct?
     [✅ Yes] [✏️ Edit] [🔄 Retry] [❌ Cancel]

User: [Taps ✅ Yes]

Bot: 📋 Task Details:
     • Task: Check the generator oil at Site B
     • Assignee: Joel
     • Time: Tomorrow 8:00 AM CST
     • Priority: Normal
     
     [✅ Submit] [✏️ Clarify] [❌ Cancel]
```

### 🔧 Technical Implementation

1. **Voice Message Handler**
   ```python
   async def handle_voice_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
       """Handle incoming voice messages."""
       voice = update.message.voice
       
       # Download voice file
       file = await context.bot.get_file(voice.file_id)
       voice_path = f"temp/voice_{update.message.from_user.id}_{voice.file_id}.ogg"
       await file.download_to_drive(voice_path)
       
       # Show processing message
       processing_msg = await update.message.reply_text(
           "🎯 Transcribing your voice message..."
       )
       
       # Transcribe using OpenAI Whisper
       try:
           transcript = await transcribe_audio(voice_path)
           await processing_msg.edit_text(
               f'🔍 I heard: "{transcript}"\n\nIs this correct?',
               reply_markup=get_voice_confirmation_keyboard()
           )
           
           # Store transcript in context for later use
           context.user_data['voice_transcript'] = transcript
           context.user_data['voice_file'] = voice_path
           
       except Exception as e:
           await processing_msg.edit_text(
               "❌ Sorry, I couldn't transcribe your message. Please try again or type your request."
           )
       finally:
           # Clean up temp file
           if os.path.exists(voice_path):
               os.remove(voice_path)
   ```

2. **OpenAI Whisper Integration**
   ```python
   async def transcribe_audio(file_path: str) -> str:
       """Transcribe audio using OpenAI Whisper API."""
       import openai
       
       with open(file_path, "rb") as audio_file:
           transcript = await openai.Audio.atranscribe(
               model="whisper-1",
               file=audio_file,
               language="en",  # Auto-detect if not specified
               response_format="text"
           )
       
       return transcript.strip()
   ```

3. **Inline Keyboard for Confirmation**
   ```python
   def get_voice_confirmation_keyboard():
       """Create confirmation keyboard for voice transcription."""
       keyboard = [
           [
               InlineKeyboardButton("✅ Yes", callback_data="voice_confirm"),
               InlineKeyboardButton("✏️ Edit", callback_data="voice_edit"),
           ],
           [
               InlineKeyboardButton("🔄 Retry", callback_data="voice_retry"),
               InlineKeyboardButton("❌ Cancel", callback_data="voice_cancel"),
           ]
       ]
       return InlineKeyboardMarkup(keyboard)
   ```

### 🎯 Advanced Features

1. **Multi-Language Support**
   - Auto-detect language from user preferences
   - Support English and Spanish initially
   - Language-specific confirmation messages

2. **Audio Preprocessing**
   - Noise reduction for field environments
   - Audio normalization
   - Split long messages into chunks

3. **Contextual Understanding**
   - Use previous messages for context
   - Learn user speech patterns
   - Common phrase shortcuts

4. **Offline Fallback**
   - Queue voice messages when offline
   - Process when connection restored
   - Local transcription option (future)

### 📊 Performance Requirements

- Transcription time: < 5 seconds for 30-second audio
- Accuracy: > 90% for clear speech
- File size limit: 25MB (Telegram limit)
- Concurrent transcriptions: Handle 10+

### 🧪 Testing Scenarios

1. **Audio Quality Tests**
   - Clear speech in quiet environment
   - Background machinery noise
   - Multiple speakers
   - Strong accents

2. **Edge Cases**
   - Very short messages (< 2 seconds)
   - Very long messages (> 2 minutes)
   - Silent audio files
   - Corrupted audio

3. **Language Tests**
   - English with technical terms
   - Spanish task descriptions
   - Mixed language input
   - Unclear pronunciation

### 🚨 Error Handling

1. **Transcription Failures**
   - Show clear error message
   - Offer retry option
   - Fallback to text input

2. **Network Issues**
   - Timeout after 30 seconds
   - Queue for retry
   - Inform user of status

3. **API Limits**
   - Track usage
   - Implement rate limiting
   - Cache recent transcriptions

### 🔌 Integration Points

- Minimal changes to existing flow
- Voice → Text → Existing parser
- Same task confirmation process
- Compatible with button UI enhancements

### 🎯 Success Metrics

- [ ] 90%+ transcription accuracy
- [ ] < 5 second processing time
- [ ] 50%+ users try voice input
- [ ] 80%+ satisfaction with voice feature