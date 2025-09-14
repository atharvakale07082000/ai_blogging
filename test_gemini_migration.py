#!/usr/bin/env python3
"""
Test script to verify Gemini 2.5 Flash migration

This script tests the basic functionality of the migrated Gemini service
to ensure everything is working correctly.
"""

import asyncio
import sys
import os
from typing import Dict, Any

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def check_environment() -> Dict[str, Any]:
    """Check if the environment is properly configured"""
    print("🔍 Checking environment configuration...")
    
    try:
        from config import settings
        
        results = {
            "gemini_api_key": bool(settings.GEMINI_API_KEY and settings.GEMINI_API_KEY != "<YOUR_GEMINI_API_KEY>"),
            "llm_provider": settings.LLM_PROVIDER.lower() == "gemini",
            "gemini_model": settings.GEMINI_MODEL == "gemini-2.5-flash",
            "dependencies": True
        }
        
        # Check if google-generativeai is installed
        try:
            import google.generativeai as genai
            print("✅ google-generativeai package is installed")
        except ImportError:
            print("❌ google-generativeai package is not installed")
            results["dependencies"] = False
        
        # Check API key
        if results["gemini_api_key"]:
            print("✅ GEMINI_API_KEY is configured")
        else:
            print("❌ GEMINI_API_KEY is not configured or is placeholder")
        
        # Check provider
        if results["llm_provider"]:
            print("✅ LLM_PROVIDER is set to 'gemini'")
        else:
            print(f"⚠️  LLM_PROVIDER is set to '{settings.LLM_PROVIDER}' (should be 'gemini')")
        
        # Check model
        if results["gemini_model"]:
            print("✅ GEMINI_MODEL is set to 'gemini-2.5-flash'")
        else:
            print(f"⚠️  GEMINI_MODEL is set to '{settings.GEMINI_MODEL}'")
        
        return results
        
    except Exception as e:
        print(f"❌ Error checking environment: {e}")
        return {"error": str(e)}


async def test_gemini_service():
    """Test the Gemini service functionality"""
    print("\n🧪 Testing Gemini service...")
    
    try:
        from services.gemini_service import GeminiService, GeminiServiceError
        
        service = GeminiService()
        
        # Test 1: Service initialization
        print("Test 1: Service initialization...")
        assert service._initialized is False
        print("✅ Service initializes correctly")
        
        # Test 2: Model info
        print("Test 2: Getting model info...")
        model_info = await service.get_model_info()
        assert "model" in model_info
        assert "provider" in model_info
        assert model_info["provider"] == "google_gemini"
        print("✅ Model info retrieved successfully")
        
        # Test 3: Prompt validation
        print("Test 3: Prompt validation...")
        try:
            await service._validate_prompt("")
            print("❌ Empty prompt validation failed")
        except ValueError:
            print("✅ Empty prompt validation works")
        
        try:
            await service._validate_prompt("Valid prompt")
            print("✅ Valid prompt validation works")
        except ValueError:
            print("❌ Valid prompt validation failed")
        
        # Test 4: Basic content generation (if API key is available)
        print("Test 4: Basic content generation...")
        try:
            content = await service.generate_blog_content(
                "Write a short sentence about AI",
                "plain"
            )
            if content and len(content) > 0:
                print("✅ Content generation works")
                print(f"   Generated: {content[:100]}...")
            else:
                print("⚠️  Content generation returned empty result")
        except GeminiServiceError as e:
            if "API" in str(e) or "key" in str(e).lower():
                print("⚠️  Content generation failed - check API key")
            else:
                print(f"❌ Content generation failed: {e}")
        except Exception as e:
            print(f"❌ Unexpected error during content generation: {e}")
        
        # Test 5: Streaming (if API key is available)
        print("Test 5: Streaming content generation...")
        try:
            chunks = []
            async for chunk in service.stream_blog_content(
                "Write a short sentence about technology",
                "plain"
            ):
                chunks.append(chunk)
            
            if chunks:
                print("✅ Streaming works")
                print(f"   Received {len(chunks)} chunks")
            else:
                print("⚠️  Streaming returned no chunks")
        except GeminiServiceError as e:
            if "API" in str(e) or "key" in str(e).lower():
                print("⚠️  Streaming failed - check API key")
            else:
                print(f"❌ Streaming failed: {e}")
        except Exception as e:
            print(f"❌ Unexpected error during streaming: {e}")
        
        await service.close()
        print("✅ Service closed successfully")
        
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import Gemini service: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error testing Gemini service: {e}")
        return False


async def test_autogen_integration():
    """Test AutoGen integration with Gemini"""
    print("\n🤖 Testing AutoGen integration...")
    
    try:
        from services.autogen_agents import llm_config
        
        # Check if AutoGen is configured to use Gemini
        if "config_list" in llm_config and len(llm_config["config_list"]) > 0:
            config = llm_config["config_list"][0]
            if "gemini" in config.get("model", "").lower():
                print("✅ AutoGen is configured to use Gemini")
                return True
            else:
                print(f"⚠️  AutoGen is configured to use: {config.get('model', 'unknown')}")
                return False
        else:
            print("❌ AutoGen configuration is missing or invalid")
            return False
            
    except Exception as e:
        print(f"❌ Error testing AutoGen integration: {e}")
        return False


def print_summary(env_results: Dict[str, Any], gemini_test: bool, autogen_test: bool):
    """Print a summary of all tests"""
    print("\n" + "="*60)
    print("📊 MIGRATION TEST SUMMARY")
    print("="*60)
    
    # Environment check
    if "error" in env_results:
        print(f"❌ Environment: FAILED - {env_results['error']}")
    else:
        env_passed = all(env_results.values())
        print(f"{'✅' if env_passed else '❌'} Environment: {'PASSED' if env_passed else 'FAILED'}")
    
    # Gemini service test
    print(f"{'✅' if gemini_test else '❌'} Gemini Service: {'PASSED' if gemini_test else 'FAILED'}")
    
    # AutoGen integration test
    print(f"{'✅' if autogen_test else '❌'} AutoGen Integration: {'PASSED' if autogen_test else 'FAILED'}")
    
    # Overall result
    all_passed = (
        "error" not in env_results and all(env_results.values()) and
        gemini_test and autogen_test
    )
    
    print("\n" + "="*60)
    if all_passed:
        print("🎉 MIGRATION SUCCESSFUL! All tests passed.")
        print("Your AI Blogging Platform is ready to use with Gemini 2.5 Flash!")
    else:
        print("⚠️  MIGRATION ISSUES DETECTED")
        print("Please check the errors above and fix them before using the platform.")
    print("="*60)


async def main():
    """Main test function"""
    print("🚀 Gemini 2.5 Flash Migration Test")
    print("="*60)
    
    # Run tests
    env_results = check_environment()
    gemini_test = await test_gemini_service()
    autogen_test = await test_autogen_integration()
    
    # Print summary
    print_summary(env_results, gemini_test, autogen_test)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with unexpected error: {e}")
        sys.exit(1)
