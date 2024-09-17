import gspread
from config import CREDENTIALS_FILENAME, QUESTIONS_SPREADSHEET_URL
from random import shuffle
from datetime import datetime


class Quizzer:
    def __init__(self, question_spreadsheet_url=QUESTIONS_SPREADSHEET_URL):
        self.account = gspread.service_account(filename=CREDENTIALS_FILENAME)
        self.url = question_spreadsheet_url
        self.spreadsheet = self.account.open_by_url(self.url)
        self.topics = {
            elem.title: elem.id for elem in self.spreadsheet.worksheets()
        }
        self.answers = self.spreadsheet.get_worksheet_by_id(self.topics.get("Results"))

    def get_topics(self):
        return {key: value for key, value in self.topics.items() if key != "Results"}

    def get_question_by_topic(self, topic_name):
        if topic_name in self.topics:
            worksheet = self.spreadsheet.get_worksheet_by_id(self.topics.get(topic_name))
            return worksheet.get_all_records()
        return []

    def questions_and_answers(self, topic_name):
        questions = self.get_question_by_topic(topic_name)
        result = []
        for elem in questions:
            answers = [elem["correct_answer"], elem["wrong_answer_1"], elem["wrong_answer_2"], elem["wrong_answer_3"]]
            shuffle(answers)
            new_format = {
                "question": elem["question"],
                "correct_answer": elem["correct_answer"],
                "answers": answers
            }
            result.append(new_format)
        return result

    def write_answer_to_result_cell(self, user_id, question, answer, correct_answer):
        index = len(list(filter(None, self.answers.col_values(1)))) + 1
        self.answers.update(f"A{index}:E{index}", [[
            user_id, question, answer, correct_answer, f"{datetime.now()}"
        ]])
