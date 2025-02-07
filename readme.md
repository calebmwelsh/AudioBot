"""
# AudioBot

AudioBot is a versatile Discord bot designed to play audio files in voice channels. It allows users to organize sound files into directories, play specific tracks, and manage playback with ease. Whether you're looking to play sound effects, music, or other audio content, AudioBot provides a seamless and user-friendly experience.

---

## Features

- **Voice Channel Management**:
  - Join and leave voice channels.
  - Stop currently playing audio.

- **Audio Playback**:
  - Play specific tracks from directories (e.g., `@AudioBot play Henchman 1`).
  - Play top-level audio files (e.g., `@AudioBot play Intro`).

- **Sound File Listing**:
  - List all available sound files and directories.
  - Expand the list to show subdirectories and files with `@AudioBot list expand`.

- **Message Cleanup**:
  - Automatically delete command and response messages after a specified delay.
  - Keeps the chat clean and clutter-free.

- **Error Handling**:
  - Provides informative error messages for invalid commands, missing files, or permission issues.

---

## Setup

### Prerequisites

- Python 3.10 or higher
- Discord Bot (To set up a Discord bot, follow the instructions in this [README](https://github.com/PointCloudLibrary/discord-bot/blob/master/README.md))
- [FFmpeg](https://ffmpeg.org/) - Multimedia framework for audio playback. Follow the [FFmpeg installation guide](https://ffmpeg.org/download.html) to install it.
- Docker (optional, for containerized deployment)

### Installation

1. Clone the repository:

```bash
git clone https://github.com/calebmwelsh/Discord-AudioBot.git
cd Discord-AudioBot
```

2. Prepare the configuration file:  
   Locate the `config.toml.temp` file in the project directory, open it, and replace the placeholder `DiscordBotToken` value with your bot's token. For example:

[General]
DiscordBotToken = "your-discord-bot-token"

3. After editing, rename the file to `config.toml` by removing the `.temp` extension.

4. Install the required dependencies:

pip install -r requirements.txt

5. Run the bot:

python main.py

---

### Running with Docker Compose

1. Create a `docker-compose.yml` file with the following content:


```yaml
version: '3.8'

services:
  discord-bot:
    image: kdidtech/discord-audio-bot:latest
    environment:
      - DISCORD_BOT_TOKEN=your-discord-bot-token-here
    restart: always
```

2. Replace `your-discord-bot-token-here` with your actual Discord bot token.

3. Start the bot using Docker Compose:

docker-compose up -d

4. Verify the bot is running:

docker-compose ps

This will automatically pull the latest image of the bot, set up the environment variables, and ensure the bot restarts automatically if it stops or the system reboots.

---

## Usage

### Commands

- **`@AudioBot join`**: Joins the voice channel you are in.
- **`@AudioBot leave`**: Leaves the current voice channel.
- **`@AudioBot play <directory> <track_number>`**: Plays a specific track from a directory (e.g., `@AudioBot play Henchman 1`).
- **`@AudioBot play <file>`**: Plays a top-level audio file (e.g., `@AudioBot play Intro`).
- **`@AudioBot stop`**: Stops the currently playing audio.
- **`@AudioBot list`**: Lists all available sound files and directories.
- **`@AudioBot list expand`**: Lists all sound files and subdirectories in an expanded tree structure.

### Example

To play a specific track from a directory, mention the bot and use the `play` command:

@AudioBot play Henchman 1

To list all available sound files:

@AudioBot list

To list all sound files and subdirectories:

@AudioBot list expand

---

## Directory Structure

AudioBot looks for audio files in the `data/audio/sounds` directory. Files can be organized into subdirectories or placed directly in the top-level directory. For example:

```bash
data/audio/sounds/  
├── Henchman/  
│   ├── Henchman_1.mp3  
│   ├── Henchman_2.mp3  
├── Villain/  
│   ├── Villain_1.mp3  
│   ├── Villain_2.mp3  
├── Intro.mp3  
├── Outro.mp3  

---
```

## License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.

---

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

---

## Acknowledgments

- [discord.py](https://discordpy.readthedocs.io/) - Python library for Discord API
- [toml](https://pypi.org/project/toml/) - Python library for TOML parsing
- [FFmpeg](https://ffmpeg.org/) - Multimedia framework for audio playback. Follow the [FFmpeg installation guide](https://ffmpeg.org/download.html) to install it.

---

Enjoy using AudioBot to enhance your Discord voice channels with audio! 🎶
"""