// Fictional rough messages for "Try an example" in Prompt mode. Each click shows the next one.
const PROMPT_EXAMPLES = [
  "hey i have a python script which works fine when i test it with a csv around 5000 rows but when i use around 500000 rows it becomes really slow and sometimes memory usage goes very high i already tried removing some columns but it didnt make much difference please explain what could be causing this and what should i check first",
  "i am making a power bi dashboard for sales performance and right now i have revenue orders average order value and customer count i also have region product category and month filters but the dashboard looks too crowded and i dont know what should be on first page and what can move to second page please suggest a good layout but keep it for management users who want quick insights",
  "i built a small rag app and it can answer some questions correctly but for a few questions it gives answers which are not actually present in the documents i am using chunk size is 500 and top k is 3 right now i want to understand whether the problem is retrieval or generation and what experiments i should run before changing everything",
  "i had a meeting with the team today and we discussed three things first the dashboard should launch next monday second we are not adding the export to excel feature in this release and third priyam will send the final data mapping by friday i wrote some notes but they are messy please turn them into a clean follow up message without changing the decisions",
];

export default PROMPT_EXAMPLES;
