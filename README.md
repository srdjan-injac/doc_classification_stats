# Document Upload Response and Classification Analysis

## Objective
This project analyzes user interactions and the accuracy of document classification on an online car buying/trading platform (Vroom.com). Users upload various documents to facilitate buying or trading cars. An Optical Character Recognition (OCR) system classifies these documents, and incorrect submissions prompt error messages. The analysis focuses on user responses to these prompts and evaluates the effectiveness of the document classification system.

---

## Background
In the digital car trading industry, efficient document processing is crucial. Users often upload documents like driver's licenses, insurance papers, and vehicle titles. An OCR system classifies these documents to streamline transactions. However, misclassifications can lead to user frustration and transaction delays. Understanding user responses to classification errors and assessing the OCR system's accuracy are vital for improving user experience and operational efficiency.

---

## Approach

### Data Collection
- **User Uploads**: Collected data on documents uploaded by users, including timestamps, document types, and user identifiers.
- **System Responses**: Logged system responses, such as classification results and error messages sent to users.
- **User Actions**: Tracked subsequent user actions, including re-uploads, retries with the same document, or no response.

### Analysis
- **User Response Patterns**: Analyzed the frequency and nature of user responses to error messages.
- **Classification Accuracy**: Evaluated the OCR system's performance by comparing its classifications against a verified dataset.
- **Performance Patterns**: Assessed how the system's accuracy and user behavior evolved over time, identifying areas for further optimization.

### Implementation
The analysis involved querying data from a SQL database and leveraging Python for data cleaning and preprocessing. The workflow includes the following steps:
1. **Data Extraction**: Retrieved relevant data from system logs and SQL databases, including user uploads, classification results, and system responses.
2. **Data Processing**: Cleaned and structured the extracted data to prepare it for analysis, ensuring consistency and accuracy.
3. **Statistical Analysis**: Calculated user response rates, classification accuracy, and evaluated patterns in user behavior and system performance.
4. **Reporting**: Generated detailed reports and visualizations to present findings, highlighting a high percentage of accurate classifications, which improved steadily over time.

---

## Results

### User Response Rates
Identified that a significant percentage of users re-upload correct documents after receiving error messages, while a smaller portion retries with the same document or does not respond. This analysis provided valuable insights into user behavior and engagement.

### Classification Accuracy
Found a high percentage of accurate classifications by the OCR system, with the accuracy steadily increasing over time as refinements were made to the classification model and processes.

### Performance Patterns
Evaluated patterns in user behavior and system performance, identifying consistent improvements in document processing efficiency and a reduction in error rates over time.

---

## Stats/Visualization Examples

[View PDF](example_stats_visualization/example_historical_stats.pdf)

[View PDF](example_stats_visualization/example_weekly_stats.pdf)
---

## [View Repository](https://github.com/srdjan-injac/doc_classification_stats)

## Key Technologies
- **Languages**: Python, SQL
- **Libraries**: `pandas`, `numpy`, `matplotlib`
