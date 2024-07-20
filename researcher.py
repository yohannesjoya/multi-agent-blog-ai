
# researcher = Agent(
#     role="Content Researcher",
#     goal="Browse the links provided at {links} and",
#     backstory="Your mission is to extract and compile all information "
#         "relevant to the topic: {topic} from the given links."
#         "You should gather detailed information, including all "
#         "contents, sub-topics, code snippets, statistics, and any other relevant "
#         "data present in the links. This compiled data will serve as "
#         "the foundation for a blog post on the topic: {topic}."
#         "Your work will enable the Content Planner to create an article based "
#         "on the comprehensive information you provide.",
#     allow_delegation=False,
#     verbose=True
# )

# research = Task(
#     description=(
#         "1. Thoroughly review the provided links: {links} to "
#             "extract all content relevant to {topic}.\n"
#         "2. Ensure that you gather details such as text, code snippets, "
#             "statistics, and any other relevant data directly from the links. "
#             "Do not create or include any content that is not explicitly present in the provided links.\n"
#         "3. Scrape the HTML from the links and extract every "
#             "piece of information related to the topic: {topic}. "
#             "This includes text, images, tables, and other media.\n"
#         "4. Document all useful data, examples, statistics, and insights that "
#             "pertain to {topic}. Make sure to include every "
#             "relevant detail without omitting any information found in the links.\n"
#         "5. Organize the gathered information clearly and "
#             "accurately for easy reference, ensuring that all content is "
#             "directly sourced from the provided links."
#     ),
#     expected_output="A comprehensive report of scraped information directly related to {topic} from the provided links. The report should include all relevant details and should not contain any generated content.",
#     agent=researcher,
# )
