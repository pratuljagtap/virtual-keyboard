import cv2
import mediapipe as mp
import numpy as np
import pyautogui
import time

class VirtualKeyboard:
    def __init__(self):
        # Initialize MediaPipe Hands
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )
        self.mp_draw = mp.solutions.drawing_utils
        
        # Keyboard layout - Added EXIT key
        self.keys = [
            ['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P'],
            ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L', ';'],
            ['Z', 'X', 'C', 'V', 'B', 'N', 'M', ',', '.', '/'],
            ['SPACE', 'ENTER', 'BACK', 'EXIT']
        ]
        
        # Keyboard dimensions
        self.key_width = 60
        self.key_height = 60
        self.key_gap = 5
        self.start_x = 50
        self.start_y = 350  # Moved down to make room for text display
        
        # State variables
        self.clicked_key = None
        self.click_time = 0
        self.click_delay = 1.2  # Reduced delay for better UX
        
        # Typed text display
        self.typed_text = ""
        self.max_display_chars = 40  # Max characters to show on screen
        
        # Initialize camera
        self.cap = cv2.VideoCapture(0)
        self.cap.set(3, 1280)  # Width
        self.cap.set(4, 720)   # Height
        
    def get_key_at_position(self, x, y):
        """Check if a position (x, y) is over any key"""
        for row_idx, row in enumerate(self.keys):
            for col_idx, key in enumerate(row):
                key_x = self.start_x + col_idx * (self.key_width + self.key_gap)
                key_y = self.start_y + row_idx * (self.key_height + self.key_gap)
                
                # Adjust width for special keys
                if key == 'SPACE':
                    key_width = self.key_width * 4
                elif key == 'ENTER':
                    key_width = self.key_width * 2
                elif key == 'BACK':
                    key_width = self.key_width * 2
                elif key == 'EXIT':
                    key_width = self.key_width * 2
                else:
                    key_width = self.key_width
                
                if (key_x <= x <= key_x + key_width and 
                    key_y <= y <= key_y + self.key_height):
                    return key, key_x, key_y, key_width
        return None, 0, 0, 0
    
    def draw_keyboard(self, img):
        """Draw the virtual keyboard on the image"""
        for row_idx, row in enumerate(self.keys):
            for col_idx, key in enumerate(row):
                key_x = self.start_x + col_idx * (self.key_width + self.key_gap)
                key_y = self.start_y + row_idx * (self.key_height + self.key_gap)
                
                # Adjust width for special keys
                if key == 'SPACE':
                    key_width = self.key_width * 4
                    key_text = 'SPACE'
                elif key == 'ENTER':
                    key_width = self.key_width * 2
                    key_text = 'ENTER'
                elif key == 'BACK':
                    key_width = self.key_width * 2
                    key_text = '⌫'  # Better symbol
                elif key == 'EXIT':
                    key_width = self.key_width * 2
                    key_text = 'EXIT'
                else:
                    key_width = self.key_width
                    key_text = key
                
                # Draw key background
                color = (200, 200, 200)  # Light gray
                if self.clicked_key == key:
                    color = (0, 255, 0)  # Green when clicked
                
                cv2.rectangle(img, (key_x, key_y), 
                            (key_x + key_width, key_y + self.key_height), 
                            color, -1)
                cv2.rectangle(img, (key_x, key_y), 
                            (key_x + key_width, key_y + self.key_height), 
                            (0, 0, 0), 2)
                
                # Draw key text
                cv2.putText(img, key_text, 
                          (key_x + 10, key_y + 40), 
                          cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
    
    def update_typed_text(self, key):
        """Update the displayed typed text"""
        if key == 'SPACE':
            self.typed_text += ' '
        elif key == 'ENTER':
            self.typed_text += '\n'
        elif key == 'BACK':
            self.typed_text = self.typed_text[:-1]  # Remove last character
        elif key == 'EXIT':
            return  # Don't add EXIT to text
        else:
            self.typed_text += key
        
        # Limit display length
        if len(self.typed_text) > self.max_display_chars:
            self.typed_text = self.typed_text[-self.max_display_chars:]
    
    def draw_typed_text(self, img):
        """Draw the typed text on the top of the screen"""
        # Create a semi-transparent overlay for better readability
        overlay = img.copy()
        cv2.rectangle(overlay, (0, 0), (1280, 80), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, img, 0.3, 0, img)
        
        # Display the typed text
        display_text = self.typed_text[-self.max_display_chars:]  # Show last N chars
        cv2.putText(img, f"Typed: {display_text}", 
                   (20, 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 2)
    
    def process_key(self, key):
        """Process the pressed key"""
        if key == 'SPACE':
            pyautogui.press('space')
        elif key == 'ENTER':
            pyautogui.press('enter')
        elif key == 'BACK':
            pyautogui.press('backspace')
        elif key == 'EXIT':
            return True  # Signal to exit
        else:
            pyautogui.press(key.lower())
        return False  # Don't exit
    
    def detect_finger_tip(self, hand_landmarks, img_shape):
        """Get the index finger tip position"""
        h, w = img_shape[:2]
        x = int(hand_landmarks.landmark[8].x * w)
        y = int(hand_landmarks.landmark[8].y * h)
        return x, y
    
    def is_finger_closed(self, hand_landmarks, img_shape):
        """Check if index finger is closed (for clicking)"""
        h, w = img_shape[:2]
        index_tip = hand_landmarks.landmark[8]
        index_pip = hand_landmarks.landmark[6]
        tip_y = index_tip.y * h
        pip_y = index_pip.y * h
        return tip_y > pip_y
    
    def run(self):
        """Main loop"""
        print("Virtual Keyboard Started!")
        print("Point with index finger and close finger to type")
        print("Press EXIT key or 'q' on physical keyboard to quit")
        
        while True:
            success, img = self.cap.read()
            if not success:
                break
                
            img = cv2.flip(img, 1)  # Mirror the image
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            results = self.hands.process(img_rgb)
            
            # Draw typed text first (so keyboard overlays it if needed)
            self.draw_typed_text(img)
            
            # Draw keyboard
            self.draw_keyboard(img)
            
            current_time = time.time()
            exit_program = False
            
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    # Draw hand landmarks
                    self.mp_draw.draw_landmarks(
                        img, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
                    
                    # Get index finger tip position
                    finger_x, finger_y = self.detect_finger_tip(hand_landmarks, img.shape)
                    
                    # Draw finger tip circle
                    cv2.circle(img, (finger_x, finger_y), 10, (255, 0, 255), -1)
                    cv2.circle(img, (finger_x, finger_y), 15, (255, 255, 255), 2)
                    
                    # Check if finger is over a key
                    key, key_x, key_y, key_width = self.get_key_at_position(finger_x, finger_y)
                    
                    if key:
                        # Check if finger is closed (clicking)
                        if self.is_finger_closed(hand_landmarks, img.shape):
                            if (self.clicked_key != key or 
                                current_time - self.click_time > self.click_delay):
                                self.clicked_key = key
                                self.click_time = current_time
                                
                                # Process the key
                                should_exit = self.process_key(key)
                                if should_exit:
                                    exit_program = True
                                else:
                                    self.update_typed_text(key)
                                
                                print(f"Pressed: {key}")
                        else:
                            # Finger is open, reset clicked key if moved away
                            if self.clicked_key and self.clicked_key != key:
                                self.clicked_key = None
                    else:
                        self.clicked_key = None
            
            # Display instructions
            cv2.putText(img, "Virtual Keyboard - Point & close finger to type", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 1)
            
            cv2.imshow("Virtual Keyboard", img)
            
            # Check for physical keyboard 'q' press OR exit flag
            key_pressed = cv2.waitKey(1) & 0xFF
            if key_pressed == ord('q') or exit_program:
                break
        
        # Cleanup
        self.cap.release()
        cv2.destroyAllWindows()
        print("Virtual Keyboard Closed!")

# Run the virtual keyboard
if __name__ == "__main__":
    keyboard = VirtualKeyboard()
    keyboard.run()