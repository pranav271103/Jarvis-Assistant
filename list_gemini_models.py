"""
Script to list all available Gemini models using your API key.
"""
import os
import google.generativeai as genai
from dotenv import load_dotenv

def list_available_models():
    """List all available Gemini models using the configured API key."""
    # Load environment variables
    load_dotenv()
    
    # Get API key from environment variables
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("Error: GEMINI_API_KEY not found in environment variables.")
        print("Please set it in your .env file or environment variables.")
        return
    
    try:
        # Configure the API key
        genai.configure(api_key=api_key)
        
        # List all available models
        print("Fetching available models...\n")
        models = genai.list_models()
        
        # Filter for Gemini models and display their details
        gemini_models = [m for m in models if 'gemini' in m.name.lower()]
        
        if not gemini_models:
            print("No Gemini models found. You might not have access to any Gemini models with this API key.")
            return
            
        print(f"Found {len(gemini_models)} Gemini models:\n")
        
        # Display model information in a table
        print(f"{'Model Name':<40} | {'Description':<30} | {'Input Tokens':<12} | {'Output Tokens'}")
        print("-" * 100)
        
        for model in gemini_models:
            name = model.name.split('/')[-1]  # Extract just the model name
            description = model.description[:80] + '...' if model.description else 'No description'
            input_token_limit = str(getattr(model, 'input_token_limit', 'N/A'))
            output_token_limit = str(getattr(model, 'output_token_limit', 'N/A'))
            
            print(f"{name:<40} | {description:<30} | {input_token_limit:<12} | {output_token_limit}")
        
        print("\nNote: Token limits and availability may vary based on your API key's permissions.")
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        print("\nPlease check your internet connection and API key validity.")

if __name__ == "__main__":
    list_available_models()
