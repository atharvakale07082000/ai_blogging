#!/usr/bin/env python3
"""
Example usage of the GeminiService with Google Gemini 2.5 Flash

This file demonstrates how to use the enhanced Gemini service
with all its features including error handling, different output formats,
and proper async patterns using Google's Generative AI package.
"""

import asyncio
import sys
import os

# Add the parent directory to the path so we can import the service
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.gemini_service import GeminiService, GeminiServiceError
from config import settings


async def example_basic_streaming():
    """Example of basic streaming blog content generation"""
    print("=== Basic Streaming Example ===")
    
    service = GeminiService()
    
    try:
        prompt = "Write a blog post about the benefits of artificial intelligence in healthcare"
        
        print(f"Generating blog content for: {prompt}")
        print("Streaming response:")
        print("-" * 50)
        
        async for chunk in service.stream_blog_content(prompt, "html"):
            print(chunk, end="", flush=True)
        
        print("\n" + "-" * 50)
        print("Streaming completed successfully!")
        
    except GeminiServiceError as e:
        print(f"Service error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        await service.close()


async def example_different_formats():
    """Example of generating content in different formats"""
    print("\n=== Different Output Formats Example ===")
    
    service = GeminiService()
    
    try:
        prompt = "Explain the concept of machine learning in simple terms"
        
        # Generate HTML format
        print("Generating HTML format:")
        html_content = await service.generate_blog_content(prompt, "html")
        print(f"HTML length: {len(html_content)} characters")
        print(f"First 100 chars: {html_content[:100]}...")
        
        # Generate Markdown format
        print("\nGenerating Markdown format:")
        markdown_content = await service.generate_blog_content(prompt, "markdown")
        print(f"Markdown length: {len(markdown_content)} characters")
        print(f"First 100 chars: {markdown_content[:100]}...")
        
        # Generate Plain text format
        print("\nGenerating Plain text format:")
        plain_content = await service.generate_blog_content(prompt, "plain")
        print(f"Plain text length: {len(plain_content)} characters")
        print(f"First 100 chars: {plain_content[:100]}...")
        
    except GeminiServiceError as e:
        print(f"Service error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        await service.close()


async def example_error_handling():
    """Example of error handling scenarios"""
    print("\n=== Error Handling Example ===")
    
    service = GeminiService()
    
    try:
        # Test with empty prompt
        print("Testing empty prompt validation:")
        try:
            await service.generate_blog_content("", "html")
        except ValueError as e:
            print(f"✓ Caught expected error: {e}")
        
        # Test with very long prompt
        print("\nTesting very long prompt validation:")
        long_prompt = "x" * 2001
        try:
            await service.generate_blog_content(long_prompt, "html")
        except ValueError as e:
            print(f"✓ Caught expected error: {e}")
        
        # Test with invalid output format
        print("\nTesting invalid output format:")
        try:
            await service.generate_blog_content("test prompt", "invalid_format")
        except ValueError as e:
            print(f"✓ Caught expected error: {e}")
        
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        await service.close()


async def example_model_info():
    """Example of getting model information"""
    print("\n=== Model Information Example ===")
    
    service = GeminiService()
    
    try:
        # Get default model info
        print("Getting default model info:")
        default_info = await service.get_model_info()
        print(f"Default model: {default_info}")
        
        # Get specific model info
        print("\nGetting specific model info:")
        specific_info = await service.get_model_info("gemini-2.5-flash")
        print(f"Specific model: {specific_info}")
        
    except GeminiServiceError as e:
        print(f"Service error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        await service.close()


async def example_concurrent_requests():
    """Example of handling concurrent requests"""
    print("\n=== Concurrent Requests Example ===")
    
    service = GeminiService()
    
    try:
        prompts = [
            "Write about renewable energy",
            "Explain blockchain technology",
            "Describe the future of remote work"
        ]
        
        print(f"Generating content for {len(prompts)} concurrent requests...")
        
        # Create tasks for concurrent execution
        tasks = [
            service.generate_blog_content(prompt, "html")
            for prompt in prompts
        ]
        
        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"Request {i+1} failed: {result}")
            else:
                print(f"Request {i+1} completed: {len(result)} characters")
        
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        await service.close()


async def example_backward_compatibility():
    """Example of using the backward compatibility function"""
    print("\n=== Backward Compatibility Example ===")
    
    from services.gemini_service import stream_blog_from_gemini
    
    try:
        prompt = "Write a short blog post about Python programming"
        
        print(f"Using backward compatibility function for: {prompt}")
        print("Streaming response:")
        print("-" * 50)
        
        async for chunk in stream_blog_from_gemini(prompt):
            print(chunk, end="", flush=True)
        
        print("\n" + "-" * 50)
        print("Backward compatibility function completed!")
        
    except Exception as e:
        print(f"Error: {e}")


async def example_blog_topics():
    """Example with various blog topics to showcase Gemini's capabilities"""
    print("\n=== Blog Topics Example ===")
    
    service = GeminiService()
    
    try:
        topics = [
            "The future of quantum computing",
            "Sustainable living tips for beginners",
            "How to start a successful online business"
        ]
        
        for i, topic in enumerate(topics, 1):
            print(f"\n--- Topic {i}: {topic} ---")
            content = await service.generate_blog_content(
                f"Write an engaging blog post about: {topic}",
                "html"
            )
            print(f"Generated {len(content)} characters")
            print(f"Preview: {content[:150]}...")
        
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        await service.close()


async def main():
    """Main function to run all examples"""
    print("🚀 GeminiService Examples with Google Gemini 2.5 Flash")
    print("=" * 60)
    
    # Check if Gemini API key is available
    if not settings.GEMINI_API_KEY:
        print("⚠️  GEMINI_API_KEY not found in configuration")
        print("Please set your Gemini API key in the .env file")
        return
    
    try:
        # Run examples
        await example_basic_streaming()
        await example_different_formats()
        await example_error_handling()
        await example_model_info()
        await example_concurrent_requests()
        await example_backward_compatibility()
        await example_blog_topics()
        
        print("\n🎉 All examples completed successfully!")
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Examples interrupted by user")
    except Exception as e:
        print(f"\n❌ Examples failed with error: {e}")


if __name__ == "__main__":
    # Run the examples
    asyncio.run(main())
