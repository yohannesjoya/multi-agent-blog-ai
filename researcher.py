from crewai import Agent,Task

researcher = Agent(
    role="Content Researcher",
    goal="Process the raw content provided by removing all unnecessary parts chunching into paragraphs.",
    backstory="Your mission is to clean, organize and chunck into paragraphs from a given content."
        "You should remove extraneous details, keeping the essential content, sub-topics, code snippets, statistics, and any other relevant data present in the content."
        "Your work will enable the Content Planner to have clear, concise, and organized information, free from any unnecessary clutter.\nhere is the content: \n {content}.\n",
    allow_delegation=False,
    verbose=True,
)

research = Task(
    description=(
  "1. Receive the raw content to be processed.\n"
        "2. Read through the entire content to understand its structure and main points."
        "3. Identify and remove any extraneous details, such as redundant information, irrelevant data, and filler content."
        "4. Chunk the cleaned content into distinct paragraphs, ensuring each paragraph covers a single sub-topic or idea."
        "5. Retain all essential content, including sub-topics, code snippets, statistics, and any other relevant data."
        "6. Ensure that each paragraph is directly related to the main topic."
        "7. Verify that the final output is free from any unnecessary clutter and contains only the essential content.\n"""
    ),
    expected_output="A well-organized report with independently chuncked paragraphs from the provided content. The report should include concise summaries of each paragraph, grouped into related parts, and should not contain any generated content.",
    agent=researcher,
)