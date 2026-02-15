
import asyncio
import logging
from services.prospect_discovery_service import ProspectDiscoveryService
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    load_dotenv()
    
    company_description = "We are an AI startup building autonomous SDR agents for B2B sales teams. We help automate lead research and outreach."
    goal = "Find Head of Sales or Sales Development Managers at B2B SaaS companies who might be interested in automating their SDR function."
    job_titles = ["Head of Sales", "SDR Manager", "Director of Sales Development"]
    
    logger.info("Starting prospect discovery test...")
    logger.info(f"Goal: {goal}")
    
    service = ProspectDiscoveryService()
    try:
        prospects = await service.discover_prospects(company_description, goal, job_titles)
        
        logger.info(f"Discovery complete. Found {len(prospects)} prospects.")
        for p in prospects:
            print("-" * 50)
            print(f"Name: {p.get('name')}")
            print(f"Role: {p.get('role')}")
            print(f"Company: {p.get('company')}")
            print(f"Score: {p.get('alignment_score')}")
            print(f"Source: {p.get('source')}")
            print(f"Reason: {p.get('reason')}")
            
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
