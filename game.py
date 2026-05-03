import random
from typing import List, Tuple, Optional

class BingoGame:
    def __init__(self):
        self.numbers = list(range(1, 76))  # 1-75
        self.called_numbers = []
    
    @staticmethod
    def generate_card() -> List[List[int]]:
        """
        Generate a 5x5 bingo card with numbers 1-75
        Center is FREE (represented as 0)
        
        Column ranges:
        B: 1-15, I: 16-30, N: 31-45, G: 46-60, O: 61-75
        """
        card = []
        ranges = [
            (1, 15),    # B
            (16, 30),   # I
            (31, 45),   # N
            (46, 60),   # G
            (61, 75)    # O
        ]
        
        for col_idx, (start, end) in enumerate(ranges):
            column = random.sample(range(start, end + 1), 5)
            card.append(column)
        
        # Transpose to get rows
        card = [[card[col][row] for col in range(5)] for row in range(5)]
        
        # Set center as FREE (0)
        card[2][2] = 0
        
        return card
    
    def call_number(self, called_numbers: List[int]) -> Optional[int]:
        """
        Call a random number that hasn't been called yet
        
        Args:
            called_numbers: List of already called numbers
            
        Returns:
            The called number or None if all numbers have been called
        """
        available = [n for n in self.numbers if n not in called_numbers]
        if not available:
            return None
        return random.choice(available)
    
    @staticmethod
    def mark_number(card: List[List[int]], marked: List[int], number: int) -> List[int]:
        """
        Mark a number on the card if it exists
        
        Args:
            card: The bingo card
            marked: List of already marked positions (as flat indices 0-24)
            number: The number to mark
            
        Returns:
            Updated list of marked positions
        """
        for row_idx, row in enumerate(card):
            for col_idx, cell in enumerate(row):
                if cell == number:
                    flat_idx = row_idx * 5 + col_idx
                    if flat_idx not in marked:
                        marked.append(flat_idx)
        return marked
    
    @staticmethod
    def check_win(card: List[List[int]], marked: List[int]) -> bool:
        """
        Check if the card has a winning pattern
        
        Winning patterns:
        - Any complete row
        - Any complete column
        - Any diagonal
        
        Args:
            card: The bingo card
            marked: List of marked positions (as flat indices 0-24)
            
        Returns:
            True if there's a winning pattern
        """
        # Convert flat indices to 2D coordinates
        marked_coords = {(idx // 5, idx % 5) for idx in marked}
        
        # Center is always marked (FREE)
        marked_coords.add((2, 2))
        
        # Check rows
        for row in range(5):
            if all((row, col) in marked_coords for col in range(5)):
                return True
        
        # Check columns
        for col in range(5):
            if all((row, col) in marked_coords for row in range(5)):
                return True
        
        # Check diagonal (top-left to bottom-right)
        if all((i, i) in marked_coords for i in range(5)):
            return True
        
        # Check diagonal (top-right to bottom-left)
        if all((i, 4 - i) in marked_coords for i in range(5)):
            return True
        
        return False
    
    @staticmethod
    def format_card(card: List[List[int]], marked: List[int] = None) -> str:
        """
        Format the bingo card for display
        
        Args:
            card: The bingo card
            marked: List of marked positions (optional)
            
        Returns:
            Formatted string representation of the card
        """
        if marked is None:
            marked = []
        
        marked_coords = {(idx // 5, idx % 5) for idx in marked}
        # Center is always marked
        marked_coords.add((2, 2))
        
        header = "  B    I    N    G    O\n"
        header += "━" * 27 + "\n"
        
        rows = []
        for row_idx, row in enumerate(card):
            row_str = ""
            for col_idx, num in enumerate(row):
                if num == 0:
                    cell = "FREE"
                else:
                    cell = f"{num:2d}"
                
                # Mark with ✓ if marked
                if (row_idx, col_idx) in marked_coords:
                    cell = f"[{cell}]" if num != 0 else "[FR]"
                else:
                    cell = f" {cell} " if num != 0 else "FREE"
                
                row_str += cell + " "
            rows.append(row_str.strip())
        
        return header + "\n".join(rows)
