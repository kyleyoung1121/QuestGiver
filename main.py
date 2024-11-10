import random
import json

# Text to speech
import pyttsx3
from gtts import gTTS
from pydub import AudioSegment
from io import BytesIO
from pygame import mixer  # Use pygame to play in-memory audio
mixer.init()
text_to_speech = pyttsx3.init()
voices = text_to_speech.getProperty('voices')
text_to_speech.setProperty('voice', voices[1].id)
previous_message = ""

# Speech recognition
import speech_recognition as sr
speech_recognizer = sr.Recognizer()

quest_data = {}
user_data = {}
current_user = None

current_goal = None


# Function to load user data from the JSON file
def load_quest_data(filename="quest_data.json"):
    global quest_data
    with open(filename, "r") as file:
        quest_data = json.load(file)
    print("Quest data loaded successfully.")
        

# Function to save changes back to the JSON file
def save_quest_data(filename="quest_data.json"):
    global quest_data
    # Save changes back to JSON file
    with open(filename, "w") as file:
        json.dump(quest_data, file, indent=4)


# Function to load user data from the JSON file
def load_user_data(filename="user_data.json"):
    global user_data, current_user
    try:
        with open(filename, "r") as file:
            user_data = json.load(file)
        print("User data loaded successfully.")
    except FileNotFoundError:
        print(f"{filename} not found. Starting with an empty user data.")
        user_data = {"users": []}
    
    # Check if there are users in user_data and set the first user as the default current user
    if user_data.get("users"):
        current_user = user_data["users"][0]
        print("Default user set to:", current_user["name"])
    else:
        print("No users available to set as current user.")
        current_user = None


# Function to save changes back to the JSON file
def save_user_data(filename="user_data.json"):
    global user_data
    # Save changes back to JSON file
    with open(filename, "w") as file:
        json.dump(user_data, file, indent=4)


def capture_voice_input():
    with sr.Microphone() as source:
        audio = speech_recognizer.listen(source)
    return audio


def convert_voice_to_text(audio):
    try:
        text = speech_recognizer.recognize_google(audio)
        print("You said: " + text)
    except sr.UnknownValueError:
        text = ""
    except sr.RequestError as e:
        text = ""
        print("Error; {0}".format(e))
    return text


# def say_text(input_text):
#     # Optional: Print out the text to the terminal as well
#     print(input_text)
#     text_to_speech.say(input_text)
#     text_to_speech.runAndWait()
#     global previous_message 
#     previous_message = input_text


def say_text(text, pitch_shift=-4):
    # Convert text to speech and save to memory
    tts = gTTS(text=text, lang='en', slow=False)
    audio_data = BytesIO()
    tts.write_to_fp(audio_data)
    audio_data.seek(0)
    
    # Load audio into pydub and shift pitch
    audio = AudioSegment.from_file(audio_data, format="mp3")
    shifted_audio = audio._spawn(audio.raw_data, overrides={
        "frame_rate": int(audio.frame_rate * (2.0 ** (pitch_shift / 12)))
    }).set_frame_rate(audio.frame_rate)
    
    # Save shifted audio to BytesIO and play with pygame
    temp_audio = BytesIO()
    shifted_audio.export(temp_audio, format="mp3")
    temp_audio.seek(0)
    mixer.music.load(temp_audio, 'mp3')
    mixer.music.play()
    
    # Wait until playback is done
    while mixer.music.get_busy():
        pass


def capture_user_response(options = None):
    while True:
        # Start listening
        captured_audio = capture_voice_input()
        text = convert_voice_to_text(captured_audio).lower()

        # Only continue if text is heard
        if text:
            # If this function is called with options, those are the only valid responses
            if options:
                # If the user says one of the valid options, return the corresponding option
                for option in options:
                    if option.lower() in text:
                        return option.lower()
                # If the user's input doesn't match the valid options, let them know
                valid_options = ""
                for option in options:
                    if valid_options:
                        valid_options += ", or "
                    valid_options += option
                say_text("Sorry, I don't understand. You may say: " + valid_options)
            
            # If no options are specified, we don't need to verify the user's input. Return the first thing we see.
            else:
                return text


def user_quest_status_check():
    global current_goal
    # Check if this user has an ongoing quest
    if current_user.get("assigned_quest", None):
        say_text("Have you completed your quest?")
        say_text(current_user.get("assigned_quest").get("quest_text"))
        user_response = capture_user_response(["yes", "no"])
        if user_response == "yes":
            xp_gained = current_user.get("assigned_quest").get("quest_xp")
            say_text(f"Congratulations! You have earned {xp_gained} XP. Would you like another quest?")
            current_user["assigned_quest"] = {}
            current_user["xp"] = int(current_user.get("xp")) + int(xp_gained)
            save_user_data()
            
            user_response = capture_user_response(["yes", "no"])
            if user_response == "yes":
                current_goal = "get_quest"
            else:
                users_current_xp = current_user.get("xp")
                say_text(f"Great! You now have {users_current_xp} XP. Good luck on your adventures!")
        else:
            say_text("Okay.")


def log_in_user():
    global current_user
    while True:
        say_text("Please say your name")
        name_input = capture_user_response()

        user_found = False
        for user in user_data.get("users", []):
            
            if user.get("name", "").lower() in name_input.lower():
                # If a match is found, this could set the current user
                current_user = user
                say_text(f"User {current_user['name']} is now logged in.")
                user_found = True
                break

        if user_found:
            break

        # Otherwise, we should check if the user entered the right name 
        say_text("User not found. Did you mean to say " + name_input + "?")
        user_response = capture_user_response(["yes", "no"])

        if user_response == "yes":
            say_text("Would you like to create a new user with this name?")
            user_response = capture_user_response(["yes", "no"])

            # Create a new user if the response is "yes"
            if user_response == "yes":
                # Append the new user to user_data and set as current user
                new_user = {
                    "name": name_input,
                    "assigned_quest": {},
                    "xp": 0,
                    "streak_count": 0
                }
                user_data["users"].append(new_user)
                current_user = new_user
                say_text(f"User {new_user['name']} has been created and logged in.")
                save_user_data()
                break


def main():
    load_quest_data()
    load_user_data()
    sleeping = False
    end_program = False
    text = ""
    global current_user
    global current_goal

    while not end_program:

        # Simple loop to idle until removed from sleep state
        while sleeping:
            button_simulation = input("Robot asleep. Press button to wake")
            if button_simulation:
                sleeping = False

        # After waking, greet the user
        say_text(random.choice([
            "Greetings!",
            "Good day.",
            "Welcome back"
        ]))
        
        # Confirm that the user has not changed
        say_text("Are you " + str(current_user["name"] + "?"))
        user_response = capture_user_response(["yes", "no"])

        # Assist the user in logging in
        if user_response == "no":
            log_in_user()

        say_text("Hello " + current_user["name"] + "!")

        user_quest_status_check()

        # Resolve main commands
        while True:

            # If we haven't determined what to do next, anticipate a command from the user.
            while not current_goal:
                # Start listening
                user_command = capture_user_response()

                if any(word in user_command.lower() for word in ["change", "switch"]):
                    if any(word in user_command.lower() for word in ["user", "account", "profile"]):
                        current_goal = "change_user"
                
                elif any(word in user_command.lower() for word in ["add"]):
                    if any(word in user_command.lower() for word in ["quest", "adventure", "test", "quiz"]): # test and quiz sound like quest
                        current_goal = "add_quest"
                
                elif any(word in user_command.lower() for word in ["get", "give"]):
                    if any(word in user_command.lower() for word in ["quest", "adventure", "test", "quiz"]): # test and quiz sound like quest
                        current_goal = "get_quest"
                
                elif any(word in user_command.lower() for word in ["help"]):
                    say_text("You can say the following commands: Change user... Add quest... Get quest...")

            # Change user
            if current_goal == "change_user":
                log_in_user()
                current_goal = None
                user_quest_status_check()

            elif current_goal == "add_quest":
                quest_description = ""
                while True:
                    say_text("In about 10 words or less, please describe your quest that you would like to add")
                    quest_description = capture_user_response()
                    say_text("I heard: " + quest_description + "... Is that correct?")
                    user_response = capture_user_response(["yes", "no"])
                    if user_response == "yes":
                        break
                
                say_text("Got it! ...")
                quest_challenge = "trivial" # default
                
                while True:
                    say_text("Would you describe your quest as trivial, easy, medium, hard, or extreme?")
                    quest_challenge = capture_user_response(["trivial", "easy", "medium", "hard", "extreme"])
                    say_text("I heard: " + quest_challenge + "... Is that correct?")
                    user_response = capture_user_response(["yes", "no"])
                    if user_response == "yes":
                        break

                quest_xp = 50 # default
                match quest_challenge:
                    case "trivial":
                        quest_xp = 50
                    case "easy":
                        quest_xp = 100
                    case "medium":
                        quest_xp = 200
                    case "hard":
                        quest_xp = 400
                    case "extreme":
                        quest_xp = 800
                
                say_text("Okay! ...")
                quest_scope = current_user["name"] # default
                say_text("Surely, this quest applies to you. But does it also apply to all users?")
                user_response = capture_user_response(["yes", "no"])
                if user_response == "yes":
                    quest_scope = "everyone"
                
                new_quest = {
                    "quest_text": quest_description,
                    "quest_xp": quest_xp,
                    "quest_scope": quest_scope
                }
                
                say_text("Nice! ... What category does your quest have? chores, adventure, wellness, or party?")
                quest_category = capture_user_response(["chores", "adventure", "wellness", "party"])
                
                say_text("Adding a " + quest_challenge + " quest for " + str(quest_xp) + " XP.")

                quest_data.get("quest_categories")[quest_category].append(new_quest)
                save_quest_data()

                current_goal = None

            elif current_goal == "get_quest":
                say_text("Excellent! ... What category of quest do you want? chores, adventure, wellness, or party?")
                quest_category = capture_user_response(["chores", "adventure", "wellness", "party"])
                
                quest_pool = quest_data.get("quest_categories")[quest_category]
                while True:
                    selected_quest = random.choice(quest_pool)
                    if selected_quest["quest_scope"] == "everyone" or selected_quest["quest_scope"] == current_user["name"]:
                        break

                say_text("I have just the thing!")
                say_text("Your new quest is: " + selected_quest["quest_text"])
                say_text("Complete this quest, and I will award you with " + str(selected_quest['quest_xp']) +" XP!")
                say_text("Are you up for the challenge?")

                user_response = capture_user_response(["yes", "no"])
                if user_response == "yes":
                    say_text("I knew you were the right person for this challenge! Good luck!")
                    current_user["assigned_quest"] = selected_quest
                    save_user_data()
                else:
                    say_text("As you wish. I will grant you one quest reroll.")
                    while True:
                        selected_quest = random.choice(quest_pool)
                        if selected_quest["quest_scope"] == "everyone" or selected_quest["quest_scope"] == current_user["name"]:
                            break
                    say_text("Your new quest is: " + selected_quest["quest_text"])
                    say_text("Complete this quest, and I will award you with " + str(selected_quest['quest_xp']) +" XP!")
                    current_user["assigned_quest"] = selected_quest
                    save_user_data()

                current_goal = None
                
                
if __name__ == "__main__":
    main()