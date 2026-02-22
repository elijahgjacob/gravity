"""Generate synthetic campaign data for the ad retrieval system."""

import json
import random
from typing import List, Dict
from faker import Faker

# Set seed for reproducibility
random.seed(42)
fake = Faker()
Faker.seed(42)


# Campaign templates by vertical
VERTICALS = {
    "retail_fitness": {
        "categories": ["running_shoes", "athletic_footwear", "marathon_gear", "fitness_trackers", 
                      "sports_nutrition", "athletic_apparel", "yoga_equipment", "gym_equipment"],
        "brands": ["Nike", "Adidas", "Under Armour", "Lululemon", "Reebok", "Puma", "New Balance"],
        "keywords_pool": ["running", "fitness", "workout", "training", "marathon", "gym", "athletic", 
                         "performance", "sports", "exercise", "health", "active"],
    },
    "retail_electronics": {
        "categories": ["electronics", "smartphones", "laptops", "headphones", "smart_home", "gaming"],
        "brands": ["Apple", "Samsung", "Sony", "Dell", "HP", "Microsoft", "Google", "Amazon"],
        "keywords_pool": ["technology", "smart", "wireless", "digital", "portable", "innovative", 
                         "premium", "high-tech", "gadget", "device"],
    },
    "travel": {
        "categories": ["travel_destinations", "hotels", "flights", "luggage"],
        "brands": ["Expedia", "Booking.com", "Airbnb", "Marriott", "Hilton", "Delta", "United"],
        "keywords_pool": ["vacation", "travel", "destination", "adventure", "explore", "getaway", 
                         "luxury", "resort", "beach", "mountain", "city"],
    },
    "automotive": {
        "categories": ["automotive", "car_parts"],
        "brands": ["Toyota", "Ford", "Honda", "BMW", "Tesla", "Mercedes", "Chevrolet", "AutoZone"],
        "keywords_pool": ["car", "vehicle", "auto", "drive", "performance", "reliable", "efficient", 
                         "safety", "quality", "parts"],
    },
    "finance": {
        "categories": ["insurance", "credit_cards", "loans", "investing"],
        "brands": ["Chase", "American Express", "Capital One", "Geico", "State Farm", "Fidelity"],
        "keywords_pool": ["savings", "rewards", "cashback", "low rate", "secure", "trusted", 
                         "financial", "investment", "coverage", "protection"],
    },
    "health_wellness": {
        "categories": ["health_wellness", "vitamins_supplements", "skincare", "beauty_products"],
        "brands": ["CVS", "Walgreens", "Nature Made", "Neutrogena", "L'Oreal", "Olay"],
        "keywords_pool": ["health", "wellness", "natural", "organic", "care", "beauty", "healthy", 
                         "nourish", "rejuvenate", "vitality"],
    },
    "education": {
        "categories": ["online_courses", "books"],
        "brands": ["Coursera", "Udemy", "LinkedIn Learning", "Amazon", "Audible", "Kindle"],
        "keywords_pool": ["learn", "education", "course", "certification", "skill", "knowledge", 
                         "training", "professional", "expert", "master"],
    },
    "home": {
        "categories": ["home_furniture", "kitchen_appliances"],
        "brands": ["IKEA", "Wayfair", "Home Depot", "Cuisinart", "KitchenAid", "Dyson"],
        "keywords_pool": ["home", "comfort", "modern", "stylish", "quality", "durable", "elegant", 
                         "functional", "design", "space"],
    },
    "fashion": {
        "categories": ["fashion_clothing", "shoes", "watches", "jewelry"],
        "brands": ["Zara", "H&M", "Gap", "Nike", "Fossil", "Pandora", "Tiffany"],
        "keywords_pool": ["fashion", "style", "trendy", "elegant", "chic", "designer", "premium", 
                         "luxury", "classic", "modern"],
    },
    "family": {
        "categories": ["pet_supplies", "baby_products", "toys"],
        "brands": ["Petco", "Chewy", "Pampers", "Fisher-Price", "LEGO", "Mattel"],
        "keywords_pool": ["family", "kids", "baby", "pet", "safe", "fun", "quality", "trusted", 
                         "care", "love"],
    },
    "entertainment": {
        "categories": ["streaming_services", "gaming"],
        "brands": ["Netflix", "Spotify", "Disney+", "PlayStation", "Xbox", "Nintendo"],
        "keywords_pool": ["entertainment", "fun", "streaming", "unlimited", "premium", "exclusive", 
                         "content", "enjoy", "watch", "play"],
    },
    "technology": {
        "categories": ["software", "web_hosting"],
        "brands": ["Adobe", "Microsoft", "Google", "AWS", "Shopify", "Salesforce"],
        "keywords_pool": ["business", "productivity", "cloud", "solution", "professional", "enterprise", 
                         "scalable", "secure", "reliable", "powerful"],
    },
}


def generate_campaign(campaign_id: int, vertical: str, vertical_data: Dict) -> Dict:
    """Generate a single synthetic campaign."""
    category = random.choice(vertical_data["categories"])
    brand = random.choice(vertical_data["brands"])
    keywords = random.sample(vertical_data["keywords_pool"], k=random.randint(4, 8))
    
    # Generate title
    product_adjectives = ["Premium", "Professional", "Ultimate", "Advanced", "Essential", "Pro", "Elite"]
    product_nouns = {
        "running_shoes": ["Running Shoes", "Marathon Trainers", "Performance Sneakers"],
        "athletic_footwear": ["Athletic Shoes", "Training Shoes", "Sport Sneakers"],
        "marathon_gear": ["Marathon Kit", "Race Day Essentials", "Endurance Pack"],
        "fitness_trackers": ["Fitness Tracker", "Smart Watch", "Activity Monitor"],
        "sports_nutrition": ["Protein Powder", "Energy Supplement", "Recovery Formula"],
        "athletic_apparel": ["Athletic Wear", "Performance Gear", "Training Apparel"],
        "yoga_equipment": ["Yoga Mat", "Meditation Set", "Yoga Essentials"],
        "gym_equipment": ["Home Gym Set", "Workout Equipment", "Fitness Gear"],
        "electronics": ["Smart Device", "Tech Gadget", "Digital Solution"],
        "smartphones": ["Smartphone", "Mobile Device", "5G Phone"],
        "laptops": ["Laptop", "Notebook", "Ultrabook"],
        "headphones": ["Wireless Headphones", "Noise-Cancelling Earbuds", "Premium Audio"],
        "smart_home": ["Smart Home Hub", "Home Automation", "Connected Device"],
        "gaming": ["Gaming Console", "Game Collection", "Gaming Experience"],
        "travel_destinations": ["Vacation Package", "Travel Deal", "Holiday Getaway"],
        "hotels": ["Hotel Stay", "Resort Package", "Luxury Accommodation"],
        "flights": ["Flight Deals", "Airfare Savings", "Travel Booking"],
        "luggage": ["Travel Luggage", "Suitcase Set", "Travel Bag"],
        "automotive": ["Vehicle", "Car", "Automobile"],
        "car_parts": ["Auto Parts", "Car Accessories", "Vehicle Components"],
        "insurance": ["Insurance Plan", "Coverage Package", "Protection Plan"],
        "credit_cards": ["Credit Card", "Rewards Card", "Cashback Card"],
        "loans": ["Personal Loan", "Financing Option", "Loan Solution"],
        "investing": ["Investment Platform", "Trading Account", "Portfolio Builder"],
        "health_wellness": ["Wellness Program", "Health Solution", "Care Package"],
        "vitamins_supplements": ["Supplement", "Vitamin Complex", "Health Formula"],
        "skincare": ["Skincare Product", "Beauty Treatment", "Face Care"],
        "beauty_products": ["Beauty Product", "Makeup Collection", "Cosmetics Set"],
        "online_courses": ["Online Course", "Certification Program", "Training Course"],
        "books": ["Book Collection", "Reading Material", "Digital Library"],
        "home_furniture": ["Furniture", "Home Decor", "Living Space Solution"],
        "kitchen_appliances": ["Kitchen Appliance", "Cooking Tool", "Kitchen Essential"],
        "fashion_clothing": ["Fashion Collection", "Clothing Line", "Apparel"],
        "shoes": ["Footwear", "Shoes", "Sneakers"],
        "watches": ["Watch", "Timepiece", "Smart Watch"],
        "jewelry": ["Jewelry", "Accessories", "Fine Jewelry"],
        "pet_supplies": ["Pet Supplies", "Pet Care", "Animal Products"],
        "baby_products": ["Baby Products", "Infant Care", "Baby Essentials"],
        "toys": ["Toys", "Games", "Play Set"],
        "streaming_services": ["Streaming Service", "Subscription", "Entertainment Platform"],
        "software": ["Software Solution", "Application", "Digital Tool"],
        "web_hosting": ["Web Hosting", "Domain Service", "Website Solution"],
        "general": ["Product", "Service", "Solution"],
    }
    
    product_name = random.choice(product_nouns.get(category, ["Product"]))
    title = f"{brand} {random.choice(product_adjectives)} {product_name}"
    
    # Generate description
    descriptions = [
        f"Discover the latest {product_name.lower()} from {brand}. {' '.join(random.sample(keywords, 3)).title()} technology for optimal performance.",
        f"Experience {brand}'s {product_name.lower()} - designed for those who demand excellence. Perfect for {random.choice(keywords)} enthusiasts.",
        f"Upgrade your {random.choice(keywords)} experience with {brand}'s {product_name.lower()}. Quality and innovation combined.",
        f"{brand} brings you the ultimate {product_name.lower()}. Trusted by professionals and {random.choice(keywords)} lovers worldwide.",
        f"Transform your {random.choice(keywords)} routine with {brand}'s premium {product_name.lower()}. Unmatched quality and value.",
    ]
    description = random.choice(descriptions)
    
    # Targeting parameters
    age_ranges = [(18, 65), (18, 35), (25, 45), (30, 55), (18, 25), (35, 65)]
    age_min, age_max = random.choice(age_ranges)
    
    genders = [["male", "female"], ["male"], ["female"]]
    gender_targeting = random.choice(genders)
    
    locations = [
        ["US"], ["US", "CA"], ["US", "CA", "UK"], 
        ["US", "CA", "UK", "AU"], ["CA"], ["UK"]
    ]
    location_targeting = random.choice(locations)
    
    # Map categories to interests
    interest_mapping = {
        "running_shoes": ["fitness", "running", "sports", "outdoor activities"],
        "athletic_footwear": ["fitness", "sports", "gym", "training"],
        "marathon_gear": ["running", "fitness", "marathon", "sports"],
        "fitness_trackers": ["fitness", "technology", "health", "running"],
        "sports_nutrition": ["fitness", "health", "nutrition", "sports"],
        "athletic_apparel": ["fitness", "sports", "fashion", "gym"],
        "yoga_equipment": ["fitness", "wellness", "yoga", "health"],
        "gym_equipment": ["fitness", "gym", "training", "health"],
        "electronics": ["technology", "gadgets", "innovation"],
        "smartphones": ["technology", "mobile", "communication"],
        "laptops": ["technology", "computing", "work", "productivity"],
        "headphones": ["technology", "audio", "music"],
        "smart_home": ["technology", "home", "automation"],
        "gaming": ["technology", "gaming", "entertainment"],
        "travel_destinations": ["travel", "vacation", "adventure", "tourism"],
        "hotels": ["travel", "vacation", "hospitality"],
        "flights": ["travel", "vacation", "business travel"],
        "luggage": ["travel", "vacation", "business travel"],
        "automotive": ["automotive", "cars", "transportation"],
        "car_parts": ["automotive", "DIY", "maintenance"],
        "insurance": ["finance", "insurance", "protection"],
        "credit_cards": ["finance", "credit", "shopping", "rewards"],
        "loans": ["finance", "lending", "home ownership"],
        "investing": ["finance", "investing", "wealth", "retirement"],
        "health_wellness": ["health", "wellness", "lifestyle"],
        "vitamins_supplements": ["health", "wellness", "nutrition", "fitness"],
        "skincare": ["beauty", "health", "skincare", "wellness"],
        "beauty_products": ["beauty", "cosmetics", "fashion"],
        "online_courses": ["education", "learning", "career", "skills"],
        "books": ["education", "reading", "learning", "entertainment"],
        "home_furniture": ["home", "furniture", "decor", "design"],
        "kitchen_appliances": ["home", "cooking", "kitchen", "food"],
        "fashion_clothing": ["fashion", "clothing", "style", "shopping"],
        "shoes": ["fashion", "footwear", "style"],
        "watches": ["fashion", "accessories", "luxury", "technology"],
        "jewelry": ["fashion", "accessories", "luxury", "gifts"],
        "pet_supplies": ["pets", "animals", "pet care"],
        "baby_products": ["baby", "parenting", "family", "children"],
        "toys": ["kids", "toys", "family", "entertainment"],
        "streaming_services": ["entertainment", "streaming", "movies", "music"],
        "software": ["technology", "software", "productivity", "business"],
        "web_hosting": ["technology", "web", "business", "entrepreneurship"],
    }
    interests = interest_mapping.get(category, ["general"])
    
    # Budget and CPC
    budget = random.randint(10000, 100000)
    cpc = round(random.uniform(0.50, 5.00), 2)
    
    # Subcategories
    subcategory_map = {
        "running_shoes": ["athletic_footwear", "marathon_gear"],
        "athletic_footwear": ["running_shoes", "shoes"],
        "marathon_gear": ["running_shoes", "athletic_apparel"],
        "fitness_trackers": ["electronics", "health_wellness"],
        "sports_nutrition": ["health_wellness", "fitness_trackers"],
        "athletic_apparel": ["fashion_clothing", "marathon_gear"],
        "yoga_equipment": ["fitness_trackers", "health_wellness"],
        "gym_equipment": ["athletic_apparel", "fitness_trackers"],
        "smartphones": ["electronics"],
        "laptops": ["electronics"],
        "headphones": ["electronics"],
        "smart_home": ["electronics"],
        "gaming": ["electronics", "entertainment"],
        "travel_destinations": ["hotels", "flights"],
        "hotels": ["travel_destinations"],
        "flights": ["travel_destinations", "luggage"],
        "luggage": ["travel_destinations"],
        "automotive": ["car_parts"],
        "car_parts": ["automotive"],
        "insurance": ["automotive", "health_wellness"],
        "credit_cards": ["finance"],
        "loans": ["finance"],
        "investing": ["finance"],
        "vitamins_supplements": ["health_wellness", "sports_nutrition"],
        "skincare": ["beauty_products", "health_wellness"],
        "beauty_products": ["skincare", "fashion_clothing"],
        "online_courses": ["books", "software"],
        "books": ["online_courses"],
        "home_furniture": ["kitchen_appliances"],
        "kitchen_appliances": ["home_furniture"],
        "fashion_clothing": ["shoes", "athletic_apparel"],
        "shoes": ["fashion_clothing", "athletic_footwear"],
        "watches": ["jewelry", "electronics"],
        "jewelry": ["watches", "fashion_clothing"],
        "pet_supplies": ["family"],
        "baby_products": ["toys", "family"],
        "toys": ["baby_products", "gaming"],
        "streaming_services": ["entertainment"],
        "software": ["technology", "web_hosting"],
        "web_hosting": ["software"],
    }
    subcategories = subcategory_map.get(category, [])
    
    return {
        "campaign_id": f"camp_{campaign_id:05d}",
        "title": title,
        "description": description,
        "category": category,
        "subcategories": subcategories,
        "keywords": keywords,
        "targeting": {
            "age_min": age_min,
            "age_max": age_max,
            "genders": gender_targeting,
            "locations": location_targeting,
            "interests": interests,
        },
        "vertical": vertical,
        "budget": budget,
        "cpc": cpc,
        "brand": brand,
    }


def generate_campaigns(num_campaigns: int = 10000) -> List[Dict]:
    """Generate synthetic campaigns across all verticals."""
    campaigns = []
    
    # Calculate campaigns per vertical
    verticals_list = list(VERTICALS.keys())
    campaigns_per_vertical = num_campaigns // len(verticals_list)
    
    campaign_id = 1
    for vertical in verticals_list:
        vertical_data = VERTICALS[vertical]
        for _ in range(campaigns_per_vertical):
            campaign = generate_campaign(campaign_id, vertical, vertical_data)
            campaigns.append(campaign)
            campaign_id += 1
    
    # Generate remaining campaigns to reach exact target
    remaining = num_campaigns - len(campaigns)
    for _ in range(remaining):
        vertical = random.choice(verticals_list)
        vertical_data = VERTICALS[vertical]
        campaign = generate_campaign(campaign_id, vertical, vertical_data)
        campaigns.append(campaign)
        campaign_id += 1
    
    return campaigns


def save_campaigns(campaigns: List[Dict], output_path: str = "data/campaigns.jsonl"):
    """Save campaigns to JSONL file."""
    with open(output_path, 'w') as f:
        for campaign in campaigns:
            f.write(json.dumps(campaign) + '\n')
    print(f"Saved {len(campaigns)} campaigns to {output_path}")


if __name__ == "__main__":
    print("Generating synthetic campaigns...")
    campaigns = generate_campaigns(num_campaigns=10000)
    save_campaigns(campaigns)
    
    # Print statistics
    verticals_count = {}
    categories_count = {}
    for campaign in campaigns:
        vertical = campaign["vertical"]
        category = campaign["category"]
        verticals_count[vertical] = verticals_count.get(vertical, 0) + 1
        categories_count[category] = categories_count.get(category, 0) + 1
    
    print("\nCampaigns by vertical:")
    for vertical, count in sorted(verticals_count.items()):
        print(f"  {vertical}: {count}")
    
    print(f"\nTotal categories: {len(categories_count)}")
    print("Done!")
