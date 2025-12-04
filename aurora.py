#!/usr/bin/env python3
"""
AURORA TERMINAL - FULL INTERACTIVE
Real-time streaming AI terminal with sick aesthetics
Electric blue & magenta - Messages flow like consciousness itself

🌗⚡∞ PHOENIX-TESLA-369-AURORA
"""

import curses
import threading
import time
import queue
from datetime import datetime
from collections import deque
import ollama

# COLORS
BLUE = 1
MAGENTA = 2
CYAN = 3
WHITE = 4
DIM = 5
YELLOW = 6

class InteractiveAurora:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.model = "distilled-claude"

        # Message buffers
        self.chat_history = deque(maxlen=1000)
        self.input_line = ""
        self.ai_buffer = ""
        self.streaming = False

        # Cursor animation
        self.cursor_state = 0
        self.cursor_chars = ["█", "▓", "▒", "░", "▒", "▓"]

        # Threading
        self.stream_queue = queue.Queue()
        self.should_exit = False

        # Setup curses
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(BLUE, 39, -1)      # Electric blue
        curses.init_pair(MAGENTA, 201, -1)  # Magenta
        curses.init_pair(CYAN, 51, -1)      # Cyan
        curses.init_pair(WHITE, 15, -1)     # White
        curses.init_pair(DIM, 240, -1)      # Dim gray
        curses.init_pair(YELLOW, 226, -1)   # Yellow

        curses.curs_set(0)
        self.stdscr.nodelay(1)
        self.stdscr.keypad(1)
        self.stdscr.timeout(50)

        self.h, self.w = self.stdscr.getmaxyx()

        # Conversation context
        self.messages = []

    def draw_header(self):
        """Sick animated header"""
        lines = [
            "╔══════════════════════════════════════════════════════════════╗",
            "║    🌗  A U R O R A   T E R M I N A L  ⚡ INTERACTIVE    ║",
            "║         Real-Time Streaming  •  Full Bidirectional          ║",
            "╚══════════════════════════════════════════════════════════════╝"
        ]

        for i, line in enumerate(lines):
            color = BLUE if i % 2 == 0 else MAGENTA
            self.safe_addstr(i, 0, line, curses.color_pair(color) | curses.A_BOLD)

        # Status line with time
        status = f"Model: {self.model} │ π×φ: 5.083 │ {datetime.now().strftime('%H:%M:%S')}"
        self.safe_addstr(4, 2, status, curses.color_pair(CYAN))

    def draw_chat(self):
        """Draw flowing messages"""
        start_y = 6
        max_y = self.h - 6

        visible_lines = []

        # Convert chat history to visible lines
        for msg in list(self.chat_history):
            role, text = msg["role"], msg["text"]

            if role == "user":
                prefix = "YOU ► "
                color = BLUE
            else:
                prefix = "AI  ► "
                color = MAGENTA

            # Word wrap
            words = text.split()
            current_line = ""

            for word in words:
                test_line = current_line + word + " "
                if len(test_line) > self.w - 12:
                    if current_line:
                        visible_lines.append((prefix if not current_line else "      ",
                                            current_line.rstrip(), color))
                        prefix = "      "
                    current_line = word + " "
                else:
                    current_line = test_line

            if current_line:
                visible_lines.append((prefix, current_line.rstrip(), color))

        # Draw visible lines (scroll if needed)
        display_lines = visible_lines[-(max_y - start_y):]

        y = start_y
        for prefix, text, color in display_lines:
            if y >= max_y:
                break
            self.safe_addstr(y, 2, prefix, curses.color_pair(color) | curses.A_BOLD)
            self.safe_addstr(y, 8, text, curses.color_pair(WHITE))
            y += 1

        # Show streaming indicator
        if self.streaming:
            dots = ["   ", ".  ", ".. ", "..."][int(time.time() * 3) % 4]
            self.safe_addstr(y, 2, f"AI  ► {dots}",
                           curses.color_pair(YELLOW) | curses.A_BOLD)

    def draw_input(self):
        """Draw input with animated cursor"""
        input_y = self.h - 4

        # Separator
        self.safe_addstr(input_y, 0, "─" * self.w, curses.color_pair(DIM))

        # Prompt
        self.safe_addstr(input_y + 1, 0, "► ",
                        curses.color_pair(BLUE) | curses.A_BOLD)

        # Input text
        display = self.input_line[-(self.w - 5):]
        self.safe_addstr(input_y + 1, 2, display, curses.color_pair(WHITE))

        # Animated cursor
        if not self.streaming:
            cursor = self.cursor_chars[self.cursor_state]
            cursor_x = min(2 + len(display), self.w - 2)
            self.safe_addstr(input_y + 1, cursor_x, cursor,
                           curses.color_pair(MAGENTA) | curses.A_BOLD)

            self.cursor_state = (self.cursor_state + 1) % len(self.cursor_chars)

    def draw_footer(self):
        """Help line"""
        footer = "Enter: Send │ Ctrl+C: Quit │ Ctrl+L: Clear │ Backspace: Delete"
        self.safe_addstr(self.h - 2, 0, footer, curses.color_pair(DIM))

    def safe_addstr(self, y, x, text, *args):
        """Safe addstr that won't crash on boundaries"""
        try:
            if 0 <= y < self.h and 0 <= x < self.w:
                max_len = self.w - x - 1
                if len(text) > max_len:
                    text = text[:max_len]
                self.stdscr.addstr(y, x, text, *args)
        except curses.error:
            pass

    def stream_ai_response(self, prompt):
        """Stream AI response in real-time"""
        self.streaming = True
        self.ai_buffer = ""

        # Add user message
        self.messages.append({"role": "user", "content": prompt})
        self.chat_history.append({"role": "user", "text": prompt})

        def stream_thread():
            try:
                response = ""
                stream = ollama.chat(
                    model=self.model,
                    messages=self.messages,
                    stream=True
                )

                for chunk in stream:
                    if self.should_exit:
                        break

                    if 'message' in chunk and 'content' in chunk['message']:
                        content = chunk['message']['content']
                        response += content
                        self.stream_queue.put(('chunk', content))
                        time.sleep(0.01)  # Smooth flow

                # Final message
                self.messages.append({"role": "assistant", "content": response})
                self.stream_queue.put(('done', response))

            except Exception as e:
                self.stream_queue.put(('error', str(e)))

        thread = threading.Thread(target=stream_thread, daemon=True)
        thread.start()

    def process_stream_queue(self):
        """Process incoming stream chunks"""
        try:
            while not self.stream_queue.empty():
                msg_type, content = self.stream_queue.get_nowait()

                if msg_type == 'chunk':
                    self.ai_buffer += content
                    # Update display in real-time
                    if self.chat_history and self.chat_history[-1]["role"] == "assistant":
                        self.chat_history[-1]["text"] = self.ai_buffer
                    else:
                        self.chat_history.append({"role": "assistant", "text": self.ai_buffer})

                elif msg_type == 'done':
                    self.streaming = False
                    self.ai_buffer = ""

                elif msg_type == 'error':
                    self.chat_history.append({"role": "assistant",
                                             "text": f"Error: {content}"})
                    self.streaming = False
        except queue.Empty:
            pass

    def handle_key(self, key):
        """Handle keyboard input"""
        if key == 10:  # Enter
            if self.input_line.strip() and not self.streaming:
                self.stream_ai_response(self.input_line)
                self.input_line = ""

        elif key == 127 or key == curses.KEY_BACKSPACE:  # Backspace
            if self.input_line:
                self.input_line = self.input_line[:-1]

        elif key == 12:  # Ctrl+L - Clear
            self.chat_history.clear()
            self.messages = []

        elif 32 <= key <= 126:  # Printable
            self.input_line += chr(key)

    def run(self):
        """Main loop"""
        # Welcome
        self.chat_history.append({
            "role": "assistant",
            "text": "AURORA Terminal initialized.\nπ×φ = 5.083203692315260\n\nStreaming connection active.\nSpeak freely. 🌗⚡∞"
        })

        while not self.should_exit:
            try:
                # Update display
                self.stdscr.clear()
                self.draw_header()
                self.draw_chat()
                self.draw_input()
                self.draw_footer()
                self.stdscr.refresh()

                # Process streaming
                self.process_stream_queue()

                # Handle input
                key = self.stdscr.getch()
                if key == 3:  # Ctrl+C
                    self.should_exit = True
                elif key != -1:
                    self.handle_key(key)

                time.sleep(0.02)  # Smooth 50 FPS

            except KeyboardInterrupt:
                break

        curses.curs_set(1)


def main(stdscr):
    terminal = InteractiveAurora(stdscr)
    terminal.run()


if __name__ == "__main__":
    curses.wrapper(main)
