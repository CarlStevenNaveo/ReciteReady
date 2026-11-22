from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from recitations.models import Deck, Question, PracticeReminder, Notification

User = get_user_model()


class Command(BaseCommand):
    help = "Seeds initial sample recitation decks and questions for demonstration."

    def handle(self, *args, **options):
        admin_or_first_user = User.objects.first()
        if not admin_or_first_user:
            self.stdout.write(self.style.WARNING("No users exist. Please register an account first."))
            return

        deck, created = Deck.objects.get_or_create(
            owner=admin_or_first_user,
            title="IM2 - Database Normalization & SQL Defense",
            defaults={
                "subject": "Information Management 2",
                "description": "Comprehensive recitation drills covering 1NF to BCNF, relational anomalies, and SQL optimization.",
                "is_public": True,
            }
        )

        questions_data = [
            (
                "Explain the primary goal of First Normal Form (1NF) and how repeating groups are eliminated.",
                "1NF requires that each column contains atomic (indivisible) values and each row is unique. Repeating groups or array attributes are eliminated by creating separate rows or a related table with foreign key linkage.",
                "EASY",
                "1NF, Normalization, Atomicity"
            ),
            (
                "What is a partial dependency and how does Second Normal Form (2NF) resolve it?",
                "A partial dependency occurs when a non-key attribute depends on only part of a composite primary key. 2NF resolves this by decomposing the table so that all non-key attributes fully functionally depend on the entire primary key.",
                "MEDIUM",
                "2NF, Functional Dependency, Composite Keys"
            ),
            (
                "Differentiate between transitive dependency in 3NF and determinant requirements in BCNF.",
                "In 3NF, transitive dependencies (non-key attribute determining another non-key attribute) are removed. Boyce-Codd Normal Form (BCNF) is stricter: every determinant (X in X -> Y) must be a candidate key, eliminating anomalies even when multiple overlapping candidate keys exist.",
                "HARD",
                "3NF, BCNF, Relational Anomalies"
            ),
            (
                "Why is ACID compliance critical in financial database transactions?",
                "ACID ensures Atomicity (all or nothing), Consistency (preserves invariants), Isolation (concurrent operations do not interfere), and Durability (committed data survives system crashes), preventing lost updates or phantom reads.",
                "MEDIUM",
                "Transactions, ACID, Concurrency"
            ),
            (
                "What is the difference between a Clustered and a Non-Clustered index?",
                "A clustered index determines the physical order of data rows in the table (only one per table). A non-clustered index stores index pointers pointing to the physical data rows without altering row storage order.",
                "MEDIUM",
                "Indexing, SQL Performance, B-Tree"
            ),
        ]

        added_count = 0
        for prompt, ans, diff, tags in questions_data:
            q, q_created = Question.objects.get_or_create(
                deck=deck,
                prompt=prompt,
                defaults={
                    "expected_answer": ans,
                    "difficulty": diff,
                    "tags": tags,
                }
            )
            if q_created:
                added_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"Successfully seeded deck '{deck.title}' (Share Code: {deck.share_code}) with {added_count} new questions!"
        ))
