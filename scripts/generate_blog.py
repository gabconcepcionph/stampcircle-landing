import os
import json
import re
import random
from datetime import datetime
import google.generativeai as genai

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

    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')

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
    
    Format the output as a JSON object with these keys:
    - title: String (The blog title)
    - description: String (Meta description for SEO)
    - content_html: String (The HTML content to go inside .article-body, use <h2>, <p>, <ul>, <li>)
    - category: String (One of: 'Customer Loyalty', 'Business Strategy', 'Coffee Shops', 'Seasonal Sales', 'Loyalty Programs', 'Customer Retention')
    - excerpt: String (A 1-2 sentence summary for the blog card)
    - slug: String (URL friendly version of title, e.g., 'how-to-boost-sales')

    Ensure the tone is encouraging and practical for small business owners. Return ONLY the JSON.
    """

    response = model.generate_content(prompt)
    try:
        json_str = response.text.replace('```json', '').replace('```', '').strip()
        data = json.loads(json_str)
    except Exception as e:
        print(f"Failed to parse AI response: {e}")
        return

    # 1. Create the new HTML file
    new_filename = f"{data['slug']}.html"
    file_path = os.path.join(BLOG_DIR, new_filename)
    
    page_html = header_template
    page_html = re.sub(r'<title>.*?</title>', f"<title>{data['title']} | StampCircle</title>", page_html)
    page_html = re.sub(r'<meta name="title" content=".*?">', f'<meta name="title" content="{data["title"]}">', page_html)
    page_html = re.sub(r'<meta name="description" content=".*?">', f'<meta name="description" content="{data["description"]}">', page_html)
    
    page_html += f'\n            <h1 class="section-title">{data["title"]}</h1>'
    page_html += '\n            <p style="opacity: 0.9; margin-bottom: 3rem; font-size: 1.1rem;">⏱️ 5 min read</p>'
    page_html += f'\n            <div class="article-body">\n{data["content_html"]}\n'
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
