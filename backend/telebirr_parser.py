"""
Telebirr Receipt Parser
Parses Telebirr confirmation messages to extract transaction details.
"""

import re
from typing import Optional, Dict
from datetime import datetime


class TelebirrParser:
    """
    Parse Telebirr confirmation messages.
    
    Example Telebirr message format:
    "You have successfully sent 100.00 Birr to John Doe (0911223344).
    Transaction ID: TBR123456789. Date: 15/01/2024 10:30 AM"
    
    Or:
    "ከ John Doe (0911223344) 100.00 ብር ተቀብለዋል።
    የግብይት ቁጥር: TBR123456789. ቀን: 15/01/2024 10:30 AM"
    """
    
    # English patterns
    SENT_PATTERN = r"successfully sent\s+(\d+(?:\.\d{2})?)\s+Birr to\s+([^(]+)\((\d+)\)"
    RECEIVED_PATTERN = r"received\s+(\d+(?:\.\d{2})?)\s+Birr from\s+([^(]+)\((\d+)\)"
    
    # Amharic patterns
    SENT_PATTERN_AM = r"(\d+(?:\.\d{2})?)\s+ብር\s+ወደ\s+([^(]+)\((\d+)\)\s+ተልከዋል"
    RECEIVED_PATTERN_AM = r"ከ\s+([^(]+)\((\d+)\)\s+(\d+(?:\.\d{2})?)\s+ብር\s+ተቀብለዋል"
    
    # Transaction ID patterns
    TX_ID_PATTERN = r"(?:Transaction ID|የግብይት ቁጥር):\s*([A-Z0-9]+)"
    
    # Date patterns
    DATE_PATTERN = r"(?:Date|ቀን):\s*(\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}:\d{2}\s*(?:AM|PM)?)"
    
    # Reference/confirmation code
    REF_PATTERN = r"(?:Ref|Reference|ማጣቀሻ):\s*([A-Z0-9]+)"
    
    @staticmethod
    def parse(message: str) -> Optional[Dict[str, any]]:
        """
        Parse Telebirr message and extract transaction details.
        Returns dict with: amount, recipient_name, recipient_phone, tx_id, date, type
        Returns None if message format is not recognized.
        """
        if not message:
            return None
        
        result = {
            'amount': None,
            'recipient_name': None,
            'recipient_phone': None,
            'sender_name': None,
            'sender_phone': None,
            'tx_id': None,
            'reference': None,
            'date': None,
            'type': None,  # 'sent' or 'received'
            'raw_message': message
        }
        
        # Try to extract amount and recipient (sent money)
        sent_match = re.search(TelebirrParser.SENT_PATTERN, message, re.IGNORECASE)
        if sent_match:
            result['amount'] = float(sent_match.group(1))
            result['recipient_name'] = sent_match.group(2).strip()
            result['recipient_phone'] = sent_match.group(3).strip()
            result['type'] = 'sent'
        else:
            # Try Amharic pattern
            sent_match_am = re.search(TelebirrParser.SENT_PATTERN_AM, message)
            if sent_match_am:
                result['amount'] = float(sent_match_am.group(1))
                result['recipient_name'] = sent_match_am.group(2).strip()
                result['recipient_phone'] = sent_match_am.group(3).strip()
                result['type'] = 'sent'
        
        # Try to extract amount and sender (received money)
        received_match = re.search(TelebirrParser.RECEIVED_PATTERN, message, re.IGNORECASE)
        if received_match:
            result['amount'] = float(received_match.group(1))
            result['sender_name'] = received_match.group(2).strip()
            result['sender_phone'] = received_match.group(3).strip()
            result['type'] = 'received'
        else:
            # Try Amharic pattern
            received_match_am = re.search(TelebirrParser.RECEIVED_PATTERN_AM, message)
            if received_match_am:
                result['sender_name'] = received_match_am.group(1).strip()
                result['sender_phone'] = received_match_am.group(2).strip()
                result['amount'] = float(received_match_am.group(3))
                result['type'] = 'received'
        
        # Extract transaction ID
        tx_match = re.search(TelebirrParser.TX_ID_PATTERN, message)
        if tx_match:
            result['tx_id'] = tx_match.group(1).strip()
        
        # Extract reference
        ref_match = re.search(TelebirrParser.REF_PATTERN, message)
        if ref_match:
            result['reference'] = ref_match.group(1).strip()
        
        # Extract date
        date_match = re.search(TelebirrParser.DATE_PATTERN, message)
        if date_match:
            result['date'] = date_match.group(1).strip()
        
        # If we couldn't extract amount or type, return None
        if not result['amount'] or not result['type']:
            return None
        
        return result
    
    @staticmethod
    def validate_receipt(parsed_data: Dict, expected_amount: float, tolerance: float = 0.01) -> bool:
        """
        Validate parsed receipt against expected amount.
        Allows small tolerance for floating point comparison.
        """
        if not parsed_data or not parsed_data.get('amount'):
            return False
        
        actual_amount = parsed_data['amount']
        return abs(actual_amount - expected_amount) <= tolerance
    
    @staticmethod
    def format_phone(phone: str) -> str:
        """
        Normalize Ethiopian phone number format.
        Returns: +251XXXXXXXXX
        """
        # Remove all non-digits
        phone = re.sub(r'\D', '', phone)
        
        # If starts with 0, replace with 251
        if phone.startswith('0'):
            phone = '251' + phone[1:]
        
        # If doesn't start with 251, add it
        if not phone.startswith('251'):
            phone = '251' + phone
        
        return '+' + phone


# Example usage and tests
if __name__ == "__main__":
    # Test cases
    test_messages = [
        # English format
        "You have successfully sent 100.00 Birr to John Doe (0911223344). Transaction ID: TBR123456789. Date: 15/01/2024 10:30 AM",
        
        # Amharic format
        "ከ John Doe (0911223344) 100.00 ብር ተቀብለዋል። የግብይት ቁጥር: TBR123456789. ቀን: 15/01/2024 10:30 AM",
        
        # Variations
        "Successfully sent 50.50 Birr to Jane Smith (0922334455). Ref: TBR987654321. Date: 16/01/2024 2:45 PM",
    ]
    
    parser = TelebirrParser()
    
    for i, msg in enumerate(test_messages, 1):
        print(f"\n{'='*60}")
        print(f"Test {i}:")
        print(f"Message: {msg}")
        print(f"{'='*60}")
        
        result = parser.parse(msg)
        if result:
            print(f"✅ Parsed successfully:")
            print(f"   Type: {result['type']}")
            print(f"   Amount: {result['amount']} ETB")
            if result['type'] == 'sent':
                print(f"   Recipient: {result['recipient_name']} ({result['recipient_phone']})")
            else:
                print(f"   Sender: {result['sender_name']} ({result['sender_phone']})")
            print(f"   Transaction ID: {result['tx_id']}")
            print(f"   Date: {result['date']}")
            
            # Validate
            if parser.validate_receipt(result, 100.00):
                print(f"   ✅ Amount validated (expected 100.00)")
            else:
                print(f"   ❌ Amount mismatch (expected 100.00, got {result['amount']})")
        else:
            print("❌ Failed to parse message")

