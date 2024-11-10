import random
import json

# Text to speech
import pyttsx3
text_to_speech = pyttsx3.init()
voices = text_to_speech.getProperty('voices')
text_to_speech.setProperty('voice', voices[1].id)
previous_message = ""

# Speech recognition
import speech_recognition as sr
speech_recognizer = sr.Recognizer()

# Global variable to store user data
user_data = {}
current_user = None


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


def start_quest():
    say_text(random.choice([
        "Welcome! I have quite the quest for you...",
        "You seek a quest? Very well.",
        "Are you up for a challenge?",
    ]))

    say_text("Your quest is to call a family member you haven't heard from in a while")




def process_voice_command(text):
    if any(word in text.lower() for word in ["quest", "quiz", "adventure"]): # Note: quiz included to fix common mishearing
        start_quest()
    
    elif "repeat" in text.lower():
        say_text("Sure. " + previous_message)

    elif "goodbye" in text.lower():
        say_text("Goodbye! Have a great day!")
        return True

    else:
        if not text == "":
            say_text("Say again?")
    return False


def say_text(input_text):
    text_to_speech.say(input_text)
    text_to_speech.runAndWait()
    # Optional: Print out the text to the terminal as well
    print(input_text)
    global previous_message 
    previous_message = input_text


def capture_user_response(options = None):
    while True:
        # Start listening
        captured_audio = capture_voice_input()
        text = convert_voice_to_text(captured_audio)

        # Only continue if text is heard
        if text:
            # If this function is called with options, those are the only valid responses
            if options:
                # If the user says one of the valid options, return the corresponding option
                for option in options:
                    if option in text:
                        return option
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


def log_in_user():
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
                    "assigned_quest": "",
                    "xp": 0,
                    "streak_count": 0
                }
                user_data["users"].append(new_user)
                current_user = new_user
                say_text(f"User {new_user['name']} has been created and logged in.")
                save_user_data()
                break

def main():
    load_user_data()
    sleeping = False
    end_program = False
    text = ""
    global current_user

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

        # Check if this user has an ongoing quest
        if current_user.get("assigned_quest", ""):
            say_text("Have you completed your quest? : ")
            say_text(current_user.get("assigned_quest"))
            user_response = capture_user_response(["yes", "no"])
            if user_response == "yes":
                say_text("Congratulations! You have earned 50 XP. Would you like another quest?")
                user_response = capture_user_response(["yes", "no"])
                if user_response == "yes":
                    current_goal = "get_quest"
                else:
                    say_text("Great! You're 450 XP from level 3. Good luck on your adventures! Goodbye!")
                    current_goal = "sleep"
            else:
                say_text("Okay.")


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
                
                say_text("Adding a " + quest_challenge + " quest for " + str(quest_xp) + " XP.")
                        
                

                    

                
if __name__ == "__main__":
    main()