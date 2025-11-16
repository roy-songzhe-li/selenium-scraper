#!/usr/bin/env python3
"""
Test Supabase connection and table structure
"""
import os
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_connection():
    print("=" * 60)
    print("Testing Supabase Connection")
    print("=" * 60)
    
    # Get credentials
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    
    if not supabase_url or not supabase_key:
        print("❌ Supabase credentials not found in .env file")
        return False
    
    print(f"\nSupabase URL: {supabase_url}")
    print(f"API Key: {supabase_key[:20]}...")
    
    try:
        # Create client
        supabase = create_client(supabase_url, supabase_key)
        print("\n✅ Successfully created Supabase client")
        
        # Test connection by querying cards table
        print("\nTesting cards table...")
        response = supabase.table('cards').select("*").limit(5).execute()
        
        print(f"✅ Connected to cards table")
        print(f"Current record count: {len(response.data)} (showing first 5)")
        
        if response.data:
            print("\nSample records:")
            for i, card in enumerate(response.data, 1):
                print(f"  {i}. {card.get('name', 'N/A')} - {card.get('tag', 'N/A')}")
        else:
            print("  (No records yet)")
        
        # Test insert
        print("\n" + "=" * 60)
        print("Testing Insert")
        print("=" * 60)
        
        test_card = {
            'name': 'TEST - 2003 Pokemon Skyridge Charizard #146',
            'tag': 'Secret Rare'
        }
        
        insert_response = supabase.table('cards').upsert(test_card, on_conflict='name').execute()
        
        if insert_response.data:
            print("✅ Test insert successful")
            print(f"Inserted: {test_card['name']}")
            
            # Clean up test data
            supabase.table('cards').delete().eq('name', test_card['name']).execute()
            print("✅ Test record cleaned up")
        
        print("\n" + "=" * 60)
        print("✅ All tests passed! Ready to scrape.")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import sys
    success = test_connection()
    sys.exit(0 if success else 1)

