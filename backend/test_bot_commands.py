"""
Test bot commands manually.
Run this to verify all commands are properly configured.
"""

import asyncio
from aiogram import Bot
from app.config import get_settings

settings = get_settings()


async def test_bot_commands():
    """Test that bot commands are set correctly."""
    bot = Bot(token=settings.BOT_TOKEN)
    
    try:
        # Get bot info
        me = await bot.get_me()
        print(f"✅ Bot connected: @{me.username} (ID: {me.id})")
        print(f"   Name: {me.first_name}")
        print()
        
        # Get current commands
        commands = await bot.get_my_commands()
        print("📋 Current Bot Commands:")
        print("-" * 50)
        
        if commands:
            for cmd in commands:
                print(f"  /{cmd.command:<15} - {cmd.description}")
        else:
            print("  ❌ No commands set")
        
        print()
        print("-" * 50)
        print(f"✅ Total commands: {len(commands)}")
        
        # Expected commands
        expected = [
            "start", "play", "register", "balance", "deposit",
            "withdraw", "transfer", "invite", "bonus", "support",
            "instruction", "cancel"
        ]
        
        actual = [cmd.command for cmd in commands]
        
        # Check if all expected commands are present
        missing = set(expected) - set(actual)
        extra = set(actual) - set(expected)
        
        if missing:
            print(f"⚠️  Missing commands: {missing}")
        
        if extra:
            print(f"ℹ️  Extra commands: {extra}")
        
        if not missing and not extra:
            print("✅ All expected commands are configured!")
        
        # Get menu button
        try:
            menu_button = await bot.get_chat_menu_button()
            print()
            print(f"🎮 Menu Button: {menu_button}")
        except Exception as e:
            print(f"⚠️  Menu button: {e}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        await bot.session.close()


if __name__ == "__main__":
    print("🤖 Testing AMHABINGO Bot Commands...")
    print()
    asyncio.run(test_bot_commands())
    print()
    print("✅ Test complete!")
