# Discord Bot

This Discord bot is built using the discord.py library and includes commands for flavorizing text and splitting audio.

## Features

- Flavorize text
- Split audio files

## Setup

1. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

1.5 Install Torch at https://pytorch.org/get-started/locally/

2. Create a file named `token` in the same directory as `main.py` and paste your Discord bot token inside.

3. Ensure you have the `commands` folder with `flavorize.py` and `split_audio.py` files containing the respective command implementations.

## Usage

Run the bot using:
```python main.py```

## Commands

- `/flavorize`: Adds flavor to text (implementation details in `commands/flavorize.py`)
- `/split_audio`: Splits audio files (implementation details in `commands/split_audio.py`)

## Note

Make sure to keep your bot token confidential and do not share it publicly.