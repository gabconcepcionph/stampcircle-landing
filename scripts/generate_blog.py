import os
import json
import re
import random
from datetime import datetime
from google import genai
from google.genai import types

# Configuration - All paths are relative to the landing/ directory
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
PROMPT_FILE = "prompt.txt"
BLOG_DIR = "blog"
BLOGS_JSON = "blogs.json"
SITEMAP = "sitemap.xml"
TEMPLATE_FILE = "blog/affordable-loyalty-software-for-small-business-boost-customer-retention.html"

def generate_blog():
    if not GEMINI_API_KEY:
        print("Error: GEMINI_API_KEY not found.")
        return

    client = genai.Client(api_key=GEMINI_API_KEY)
    model_id = "gemini-2.5-flash" # Switching to 2.0 as requested/implied by package change

    # Read files with explicit encoding
    with open(PROMPT_FILE, 'r', encoding='utf-8') as f:
        prompt_instructions = f.read()

    with open(TEMPLATE_FILE, 'r', encoding='utf-8') as f:
        template_content = f.read()

    # Extract layout from template
    header_parts = template_content.split('<section class="about">')
    footer_parts = template_content.split('</ul>\n            </div>\n        </div>\n    </section>')
    
    header_template = header_parts[0] + '<section class="about">\n        <div class="about-content">'
    footer_template = '\n            <div class="article-body">\n                <h3>Related articles</h3>\n                <ul>\n' + footer_parts[1]

    prompt = f"""
    Use these instructions: {prompt_instructions}
    
    Target Audience: Philippine small business owners (SMEs), coffee shop owners, retail managers, and service providers (salons, spas) looking to improve sales and customer retention.
    
    SEO Goals:
    - Primary Keywords: 'how to increase sales for small business Philippines', 'digital stamp cards Philippines', 'customer loyalty program Philippines', 'business promotion ideas Philippines', 'improve repeat customers'.
    - Tone: Practical, encouraging, and localized for the Philippine market (mentioning local business contexts like 'ber months', 'sari-sari stores', 'local cafes', etc., where appropriate).
    
    Format the output as a JSON object with these keys:
    - title: String (SEO-friendly title using high-volume keywords, e.g., '5 Ways to Increase Your Cafe Sales in the Philippines with Digital Stamp Cards')
    - description: String (SEO meta description, max 160 chars, includes call to action)
    - content_html: String (The HTML content to go inside .article-body. Use <h2> for subheadings, <p> for paragraphs, and <ul>/<li> for lists. Naturally integrate keywords.)
    - category: String (One of: 'Customer Loyalty', 'Business Strategy', 'Coffee Shops', 'Seasonal Sales', 'Loyalty Programs', 'Customer Retention')
    - excerpt: String (A 1-2 sentence summary for the blog card, includes primary keywords)
    - slug: String (SEO-friendly URL slug, e.g., 'increase-sales-small-business-philippines-loyalty')
    - social_poster_text: String (Text for social media poster)
    - social_caption: String (Caption for social media including relevant hashtags like #SMEPhilippines #StampCircle #CustomerLoyalty)

    Return ONLY the JSON.
    """

    response = client.models.generate_content(
        model=model_id,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type='application/json',
        ),
    )
    
    try:
        data = json.loads(response.text)
    except Exception as e:
        print(f"Failed to parse AI response: {e}")
        print(f"Response text: {response.text}")
        return

    # 1. Create the new HTML file
    new_filename = f"{data['slug']}.html"
    file_path = os.path.join(BLOG_DIR, new_filename)
    
    # Calculate accurate reading time (average 200 words per minute)
    word_count = len(re.findall(r'\w+', data['content_html']))
    read_time = max(1, round(word_count / 200))

    page_html = header_template
    page_html = re.sub(r'<title>.*?</title>', f"<title>{data['title']} | StampCircle</title>", page_html)
    page_html = re.sub(r'<meta name="title" content=".*?">', f'<meta name="title" content="{data["title"]}">', page_html)
    page_html = re.sub(r'<meta name="description" content=".*?">', f'<meta name="description" content="{data["description"]}">', page_html)
    
    page_html += f'\n            <h1 class="section-title">{data["title"]}</h1>'
    page_html += f'\n            <p style="opacity: 0.9; margin-bottom: 3rem; font-size: 1.1rem;">⏱️ {read_time} min read</p>'
    page_html += f'\n            <div class="article-body">\n{data["content_html"]}\n'
    
    # Add Social Media Footnote
    page_html += f"""
                <hr style="margin: 3rem 0 2rem; border: 0; border-top: 1px solid rgba(255,255,255,0.2);">
                <div class="social-footnote" style="font-size: 0.85rem; opacity: 0.8; line-height: 1.4;">
                    <p><strong>Social Media Poster Text:</strong><br>{data.get('social_poster_text', '')}</p>
                    <p style="margin-top: 1rem;"><strong>Social Media Caption:</strong><br>{data.get('social_caption', '')}</p>
                </div>
    """
    
    page_html += footer_template

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(page_html)
    print(f"Created new blog: {file_path}")

    # 2. Update blogs.json (Add to beginning of list)
    new_post = {
        "title": data["title"],
        "href": f"blog/{new_filename}",
        "category": data["category"],
        "excerpt": data["excerpt"]
    }

    try:
        with open(BLOGS_JSON, 'r', encoding='utf-8') as f:
            posts = json.load(f)
    except Exception:
        posts = []

    posts.insert(0, new_post)

    with open(BLOGS_JSON, 'w', encoding='utf-8') as f:
        json.dump(posts, f, indent=4)
    print("Updated blogs.json")

    # 3. Update sitemap.xml
    with open(SITEMAP, 'r', encoding='utf-8') as f:
        sitemap_content = f.read()
    
    new_url = f"""  <url>
    <loc>https://stampcircle.com/blog/{new_filename}</loc>
    <lastmod>{datetime.now().strftime('%Y-%m-%d')}</lastmod>
    <priority>0.80</priority>
  </url>"""
    
    if "</urlset>" in sitemap_content:
        updated_sitemap = sitemap_content.replace("</urlset>", f"{new_url}\n</urlset>")
        with open(SITEMAP, 'w', encoding='utf-8') as f:
            f.write(updated_sitemap)
        print("Updated sitemap.xml")

if __name__ == "__main__":
    generate_blog()
