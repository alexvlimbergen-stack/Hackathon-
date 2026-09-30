### Intelligent Knowledge Database

An **Intelligent Knowledge Database** is a self-organizing knowledge system that continuously receives, processes, and structures information from multiple sources, including client input, emails, Microsoft Teams conversations, documents, and other communication channels.

Using AI, the system analyzes the **context and meaning** of incoming information. It automatically determines what information is relevant, how it should be categorized, and where it should be stored within the knowledge database.

Rather than functioning as a passive storage system, the database actively manages and evolves its own knowledge structure. When new information is received, the system determines whether it should:

* Create a new record or category
* Be added to an existing record
* Be merged with similar or related information
* Update or enrich existing information
* Replace outdated or conflicting information
* Coexist with existing information when both versions are complementary

The system continuously compares newly received information with existing knowledge to identify **similarities, relationships, duplicates, conflicts, and missing information**. This enables the database to dynamically evolve as new information becomes available.

The structure of the knowledge database is defined in an AI-readable file called **`contents.yaml`**. This file contains the instructions and structure used by the AI to determine what information should be extracted and how it should be organized. When new categories or types of information are introduced, the structure can dynamically adapt to accommodate them.

The overall goal is to create a **self-organizing knowledge system** that transforms unstructured information from everyday communication into structured, connected, and continuously updated knowledge—without requiring users to manually determine where each piece of information belongs.

### Processing an Email with an Important Attachment

When an email containing an attachment is received, the system follows several steps:

1. **Attachment scanning**
   The system analyzes the email and its attachments using predefined keywords and criteria. Based on this analysis, potentially important files are separated from files that are considered irrelevant.

2. **User validation**
   When an attachment is identified as potentially important, a pop-up is displayed. The user can provide additional parameters, such as how confident they are that the information contained in the file is accurate or reliable.

3. **Similarity and conflict detection**
   An AI-powered algorithm compares the new file with existing information in the knowledge database. It determines whether similar or related information already exists and decides whether the new information should:

   * Replace existing information,
   * Be merged with it,
   * Update or enrich it, or
   * Coexist alongside it as a separate version.

4. **Information extraction**
   Every file added to the knowledge database is automatically scanned for relevant information. The AI uses the instructions defined in **`contents.yaml`** to determine which information should be extracted.

5. **Structured storage**
   The extracted information is stored in the database together with the original file. This creates a connection between the source document and its structured knowledge, enabling more advanced searches and queries.

Through this process, the system does not simply **store files**. It continuously **interprets, connects, validates, and reorganizes information**, allowing the knowledge database to become more comprehensive and useful over time.


### Important note about Aikido security test

We encountered technical issues with the Aikido platform, which prevented us from scanning our code for potential security vulnerabilities. However, since our prototype runs entirely in a local environment and does not rely on external services or public-facing infrastructure, the potential security risks are more limited. Nevertheless, this does not eliminate the possibility of vulnerabilities within the application itself.