import os
import re
import dspy
from dspy import InputField, OutputField, ChainOfThought, Predict, Signature, Module
from dotenv import load_dotenv
from load_data import get_query_engine, load_data

load_dotenv()

# lm = dspy.GROQ(model='llama-3.1-8b-instant', api_key = os.getenv("GROQ_API_KEY") )
lm = dspy.OpenAI(model='gpt-4o-mini', api_key = os.getenv("OPENAI_API_KEY"), max_tokens=1024)

dspy.settings.configure(lm=lm)

index = load_data("data")
query_engine = get_query_engine(index)


# I want to create a project where a source document (PDF) is used to evaluate the responses generated by a large language model (LLM). The process works like this: the LLM's response will be broken down into paragraphs, and each paragraph will be searched for in the PDF using a Chroma/vector database retriever. A separate LLM agent will then assess whether the generated response is accurate based on the content of the PDF.

# So the data is loaded into a vector database. The user inputs a query (containing the response from LLM by his/her choice) and the Model will search the vector database for the relevant paragraphs. It will then tell if the response is accurate or not, if it is not accurate, it will give a detailed explanation as to why it is not accurate and then give a new response. This process will repeat until the response is accurate.

class compare_response(Signature):
    """Evaluate the generated response against the provided context, focusing on factual correctness and relevance."""
    initial_response = InputField(desc="Generated response to evaluate")
    context_response = InputField(desc="Relevant context from the document")
    accuracy = OutputField(desc="Accuracy score between 0 and 10")
    explanation = OutputField(desc="Concise explanation about why the score was given")

class response_generator(Signature):
    """Generate a corrected response based on a query and provided context. Ensure the new response is factually accurate, aligned with the context, and well-structured."""
    query = InputField(desc="Query that produced an incorrect response")
    context = InputField(desc="Relevant context from the source document")
    response = OutputField(desc="Corrected and more accurate response based on the context")

class Assessor(Module):
    def __init__(self):
        super().__init__()
        self.query_engine = query_engine
        self.compare_response = ChainOfThought(compare_response)
        self.generate_response = ChainOfThought(response_generator)

    def forward(self, initial_response: str) -> dict:
        context = self.query_engine.query(initial_response).response
        response = self.compare_response(
            initial_response=initial_response, 
            context_response=context
        )
 
        result = {}
        accuracy_score = int(float(response.accuracy))
        try:
            result['accuracy_score'] = accuracy_score
            if accuracy_score < 7:
                context = self.query_engine.query(initial_response).response
                new_response = self.generate_response(query=initial_response, context=context)
                result['response'] = new_response.response
            else:
                result['response'] = initial_response
        except Exception as e:
            result['response'] = initial_response
            result['error'] = str(e)
        return result
    

if __name__ == "__main__":
    query = "One of the key professional failings during the 1996 disaster was the inability of the teams to adapt to changing conditions. Mount Everest is an inherently unpredictable environment, and successful climbers must be able to adjust their plans based on the realities they face on the mountain. However, both the New Zealand and American teams failed to do so."
    
    query_false = "The 2000 Mt Everest climbing disaster was the deadliest year in the 43-year history of climbing Mt Everest, with a total of 10 climber deaths and several other serious injuries. This disaster underscores the critical importance of adaptability in extreme environments. Successful climbers must be able to adjust their plans based on the realities they face on the mountain. However, during the 1996 disaster, both the New Zealand and American teams struggled to adapt to the rapidly changing"

    assessor = Assessor()
    assessment = assessor(initial_response=query_false)
    print(assessment)