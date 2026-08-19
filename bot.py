import os
from dotenv import load_dotenv
import time
from datetime import date
from atproto import Client
import statsapi

load_dotenv()

# Load Bluesky login credentials
BSKY_HANDLE = os.getenv("BSKY_HANDLE")
BSKY_PASSWORD = os.getenv("BSKY_PASSWORD")

# Load Cardinals team id
TEAM_ID = int(os.getenv("TEAM_ID"))

# Track last score
LAST_SCORE = None

# Return current date in MM/DD/YYYY format
def getFormattedDate():
  today = date.today()
  formattedDate = today.strftime("%m/%d/%Y")
  return formattedDate

# Get the current game
def getLiveGame():
  date = getFormattedDate()
  game = statsapi.schedule(date=date, team=TEAM_ID)

  if game:
    return {
      "game_id": game[0]["game_id"],
      "away_name": game[0]["away_name"],
      "home_name": game[0]["home_name"],
      "away_score": game[0]["away_score"],
      "home_score": game[0]["home_score"],
      "current_inning": game[0]["current_inning"],
      "inning_state": game[0]["inning_state"]
    }

  return None

def main():
  global LAST_SCORE

  # Log in to Bluesky
  client = Client()
  client.login(BSKY_HANDLE, BSKY_PASSWORD)

  while True:
    try:
      game = getLiveGame()

      if game:
        game_id = game["game_id"]
        score = (game["away_score"], game["home_score"])

        if score != LAST_SCORE:
          # Scoring plays include the current score, but we want to build it
          # ourselves, so split into an array and just grab the scoring play
          # (penultimate entry)
          scoring_plays = statsapi.game_scoring_plays(game_id) #567074
          scoring_plays = scoring_plays.split("\n")
          play_description = scoring_plays[-2]

          # Build remaining post elements
          away_name = game["away_name"]
          home_name = game["home_name"]
          current_inning = game["current_inning"]
          inning_state = game["inning_state"]

          # Don't post Middle or End of inning
          if inning_state == "Middle":
            inning_state = "Top"
          elif inning_state == "End":
            inning_state = "Bottom"

          # Build the post
          post = (
            f"{play_description}\n\n"
            f"{away_name} {score[0]} - {score[1]} {home_name}\n"
            f"{inning_state} {current_inning}"
          )

          # Update the score we need to check against
          LAST_SCORE = score

          # Lick the stamp and send it
          client.post(post)

      # Check for a scoring update every 60 seconds
      time.sleep(60)

    except Exception as e:
      print(e)
      break

if __name__ == '__main__':
  main()