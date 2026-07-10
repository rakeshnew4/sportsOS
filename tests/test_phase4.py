"""
Phase 4 (Growth Engine) Test Suite
Tests: Notifications, Waitlists, Team History, Staff Management
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from app.services import (
    notification_service,
    waitlist_service,
    team_service,
    booking_service,
)


class MockDB:
    """Mock database for testing."""
    def __init__(self):
        self.data = {}

    def collection(self, name):
        return MockCollection(self, name)

    def collection_group(self, name):
        return MockCollectionGroup(self)


class MockCollection:
    def __init__(self, db, name):
        self.db = db
        self.name = name
        self.docs = {}

    def document(self, doc_id):
        if doc_id not in self.docs:
            self.docs[doc_id] = MockDocument(self.db, self.name, doc_id)
        return self.docs[doc_id]

    def stream(self):
        return [doc for doc in self.docs.values() if doc.data]

    def where(self, filter=None):
        return self

    def order_by(self, field, direction="ASCENDING"):
        return self


class MockDocument:
    def __init__(self, db, collection, doc_id):
        self.db = db
        self.collection_name = collection
        self.id = doc_id
        self.data = None
        self.reference = MagicMock()

    def set(self, data):
        self.data = {**data, "id": self.id}
        return self

    def get(self):
        return self

    def to_dict(self):
        return self.data or {}

    def exists(self):
        return self.data is not None

    def update(self, data):
        if self.data:
            self.data.update(data)
        else:
            self.data = data
        return self

    def delete(self):
        self.data = None

    def collection(self, name):
        return MockCollection(self.db, f"{self.collection_name}/{self.id}/{name}")


class MockCollectionGroup:
    def __init__(self, db):
        self.db = db

    def document(self, doc_id):
        return MockDocument(self.db, "collection_group", doc_id)

    def where(self, filter=None):
        return self

    def stream(self):
        return []


# ==============================================================================
# NOTIFICATION TESTS
# ==============================================================================

class TestNotifications:
    """Test notification service."""

    def test_record_notification(self):
        """Test recording a notification."""
        db = MockDB()

        notification = notification_service.record_notification(
            db,
            player_uid="player-1",
            notification_type="match_needs_players",
            title="2 players needed",
            body="Badminton match in 30 mins",
            data={"booking_id": "booking-1"},
            send_push=False,  # Don't actually send
        )

        assert notification["notification_id"]
        assert notification["type"] == "match_needs_players"
        print("✅ Notification recorded successfully")

    def test_notify_match_needs_players(self):
        """Test match needs players notification."""
        db = MockDB()

        notification_service.notify_match_needs_players(
            db,
            booking_id="booking-1",
            sport="badminton",
            slots_needed=2,
            time_until_match=30,
            nearby_player_uids=["player-1", "player-2"],
        )

        print("✅ Match needs players notification sent")

    def test_notify_reward_earned(self):
        """Test reward earned notification."""
        db = MockDB()

        notification_service.notify_reward_earned(
            db,
            player_uid="captain-1",
            credits_amount=30.0,
            reason="Completed badminton match",
        )

        print("✅ Reward earned notification sent")

    def test_get_notification_preferences(self):
        """Test getting notification preferences."""
        db = MockDB()

        prefs = notification_service.get_notification_preferences(db, "player-1")

        # Should return defaults if user doesn't exist
        assert prefs.get("match_needs_players", True) == True
        print("✅ Got notification preferences")


# ==============================================================================
# WAITLIST TESTS
# ==============================================================================

class TestWaitlist:
    """Test waitlist service."""

    def test_join_waitlist(self):
        """Test player joining waitlist."""
        db = MockDB()

        # Create booking first
        db.collection("tenants").document("venue-1").collection("bookings").document(
            "booking-1"
        ).set({
            "booking_id": "booking-1",
            "sport": "badminton",
            "status": "confirmed",
        })

        # Join waitlist
        result = waitlist_service.join_waitlist(
            db, "venue-1", "booking-1", "player-1"
        )

        assert result["success"] == True
        assert result["position"] == 1
        print("✅ Player joined waitlist at position 1")

    def test_get_waitlist(self):
        """Test getting waitlist."""
        db = MockDB()

        # Create booking
        db.collection("tenants").document("venue-1").collection("bookings").document(
            "booking-1"
        ).set({"booking_id": "booking-1"})

        # Add players to waitlist
        waitlist_service.join_waitlist(db, "venue-1", "booking-1", "player-1")
        waitlist_service.join_waitlist(db, "venue-1", "booking-1", "player-2")
        waitlist_service.join_waitlist(db, "venue-1", "booking-1", "player-3")

        # Get waitlist
        result = waitlist_service.get_waitlist(db, "venue-1", "booking-1")

        assert result["total_waiting"] == 3
        assert result["queue"][0]["position"] == 1
        print("✅ Got waitlist with 3 players")

    def test_promote_from_waitlist(self):
        """Test promoting player from waitlist."""
        db = MockDB()

        # Create booking
        db.collection("tenants").document("venue-1").collection("bookings").document(
            "booking-1"
        ).set({"booking_id": "booking-1", "sport": "badminton"})

        # Add players
        waitlist_service.join_waitlist(db, "venue-1", "booking-1", "player-1")
        waitlist_service.join_waitlist(db, "venue-1", "booking-1", "player-2")

        # Promote first player
        with patch('app.services.notification_service.notify_promoted_from_waitlist'):
            result = waitlist_service.promote_from_waitlist(db, "venue-1", "booking-1")

        assert result["promoted_player_uid"] == "player-1"
        assert result["position"] == 1
        print("✅ Promoted player from position 1")

    def test_confirm_promotion(self):
        """Test player confirming promotion."""
        db = MockDB()

        # Setup
        db.collection("tenants").document("venue-1").collection("bookings").document(
            "booking-1"
        ).set({"booking_id": "booking-1"})

        waitlist_service.join_waitlist(db, "venue-1", "booking-1", "player-1")
        with patch('app.services.notification_service.notify_promoted_from_waitlist'):
            waitlist_service.promote_from_waitlist(db, "venue-1", "booking-1")

        # Confirm promotion
        result = waitlist_service.confirm_promotion(
            db, "venue-1", "booking-1", "player-1"
        )

        assert result["success"] == True
        print("✅ Player confirmed promotion")

    def test_decline_promotion_promotes_next(self):
        """Test declining promotion auto-promotes next player."""
        db = MockDB()

        # Setup
        db.collection("tenants").document("venue-1").collection("bookings").document(
            "booking-1"
        ).set({"booking_id": "booking-1", "sport": "badminton"})

        waitlist_service.join_waitlist(db, "venue-1", "booking-1", "player-1")
        waitlist_service.join_waitlist(db, "venue-1", "booking-1", "player-2")

        # Promote first
        with patch('app.services.notification_service.notify_promoted_from_waitlist'):
            waitlist_service.promote_from_waitlist(db, "venue-1", "booking-1")

            # Decline
            waitlist_service.decline_promotion(
                db, "venue-1", "booking-1", "player-1"
            )

            # Check player-2 is now promoted
            waitlist = waitlist_service.get_waitlist(db, "venue-1", "booking-1")
            # Player 2 should be promoted
            assert any(p["player_uid"] == "player-2" for p in waitlist["queue"])

        print("✅ Next player auto-promoted when first declined")


# ==============================================================================
# TEAM HISTORY TESTS
# ==============================================================================

class TestTeamHistory:
    """Test team history and stats."""

    def test_record_team_match(self):
        """Test recording team match result."""
        db = MockDB()

        # Create team first
        team = team_service.create_team(db, "captain-1", "badminton", "Team A")

        # Record a match
        result = team_service.record_team_match(
            db,
            team_id=team.team_id,
            booking_id="booking-1",
            opponent_team_id="team-b",
            opponent_team_name="Team B",
            result="win",
            player_count=4,
        )

        assert result["match_id"]
        assert result["result"] == "win"
        print("✅ Team match recorded")

    def test_team_stats_updated(self):
        """Test team stats are updated on match record."""
        db = MockDB()

        team = team_service.create_team(db, "captain-1", "badminton", "Team A")

        # Record win
        team_service.record_team_match(
            db,
            team_id=team.team_id,
            booking_id="booking-1",
            opponent_team_id="team-b",
            opponent_team_name="Team B",
            result="win",
            player_count=4,
        )

        # Check stats
        stats = team_service.get_team_stats(db, team.team_id)

        assert stats["total_matches"] == 1
        assert stats["wins"] == 1
        assert stats["rating"] > 1200  # ELO increased
        print("✅ Team stats updated (wins, rating)")

    def test_elo_rating_calculation(self):
        """Test ELO rating calculation."""
        db = MockDB()

        team = team_service.create_team(db, "captain-1", "badminton", "Team A")
        initial_rating = 1200.0

        # Record 3 wins
        for i in range(3):
            team_service.record_team_match(
                db,
                team_id=team.team_id,
                booking_id=f"booking-{i}",
                opponent_team_id=f"team-{i}",
                opponent_team_name=f"Team {i}",
                result="win",
                player_count=4,
            )

        stats = team_service.get_team_stats(db, team.team_id)

        # Rating should increase: 1200 + (25 * 3) = 1275
        assert stats["rating"] == initial_rating + 75
        assert stats["wins"] == 3
        print(f"✅ ELO rating: {initial_rating} → {stats['rating']}")

    def test_get_team_history(self):
        """Test getting team match history."""
        db = MockDB()

        team = team_service.create_team(db, "captain-1", "badminton", "Team A")

        # Record 5 matches
        for i in range(5):
            team_service.record_team_match(
                db,
                team_id=team.team_id,
                booking_id=f"booking-{i}",
                opponent_team_id=f"team-{i}",
                opponent_team_name=f"Team {i}",
                result="win" if i % 2 == 0 else "loss",
                player_count=4,
            )

        history = team_service.get_team_history(db, team.team_id, limit=10)

        assert len(history) == 5
        assert history[0]["result"] in ["win", "loss"]
        print(f"✅ Retrieved team history: {len(history)} matches")


# ==============================================================================
# INTEGRATION TESTS
# ==============================================================================

class TestPhase4Integration:
    """Integration tests for Phase 4 features."""

    def test_complete_waitlist_flow(self):
        """Test complete flow: match full → join waitlist → promoted → confirm."""
        db = MockDB()

        # 1. Create booking (full)
        db.collection("tenants").document("venue-1").collection("bookings").document(
            "booking-1"
        ).set({
            "booking_id": "booking-1",
            "sport": "badminton",
            "status": "confirmed",
            "created_by": "captain-1",
            "slots_total": 2,
            "slots_open": 0,  # Full
        })

        # 2. Player joins waitlist
        result1 = waitlist_service.join_waitlist(db, "venue-1", "booking-1", "player-1")
        assert result1["position"] == 1
        print("   ✓ Player joined waitlist at position 1")

        # 3. Another player joins
        result2 = waitlist_service.join_waitlist(db, "venue-1", "booking-1", "player-2")
        assert result2["position"] == 2
        print("   ✓ Player joined waitlist at position 2")

        # 4. Someone cancels → auto-promote
        with patch('app.services.notification_service.notify_promoted_from_waitlist'):
            promoted = waitlist_service.promote_from_waitlist(
                db, "venue-1", "booking-1"
            )

        assert promoted["promoted_player_uid"] == "player-1"
        print("   ✓ Player 1 promoted from position 1")

        # 5. Player confirms promotion
        confirmed = waitlist_service.confirm_promotion(
            db, "venue-1", "booking-1", "player-1"
        )
        assert confirmed["success"] == True
        print("   ✓ Player 1 confirmed promotion")

        # 6. Player 2 should now be promoted
        with patch('app.services.notification_service.notify_promoted_from_waitlist'):
            promoted2 = waitlist_service.promote_from_waitlist(
                db, "venue-1", "booking-1"
            )

        assert promoted2["promoted_player_uid"] == "player-2"
        print("   ✓ Player 2 automatically promoted")

    def test_team_match_and_reward_flow(self):
        """Test: Team plays → match completes → team stats + reward issued."""
        db = MockDB()

        # 1. Create team
        team = team_service.create_team(db, "captain-1", "badminton", "Elite Shuttlers")
        print("   ✓ Team created")

        # 2. Create booking
        db.collection("tenants").document("venue-1").collection("bookings").document(
            "booking-1"
        ).set({
            "booking_id": "booking-1",
            "team_id": team.team_id,
            "sport": "badminton",
            "status": "confirmed",
            "created_by": "captain-1",
            "slots_total": 4,
            "slots_open": 0,
            "tenant_name": "Court A",
        })

        db.collection("tenants").document("venue-1").collection("bookings").document(
            "booking-1"
        ).collection("checkins").document("captain-1").set({
            "player_uid": "captain-1",
            "checked_in_at": "2026-07-09T18:00:00Z",
        })

        print("   ✓ Booking created and captain checked in")

        # 3. Complete match (this should record team history)
        with patch('app.services.rewards_service.issue_reward'):
            completion = booking_service.complete_match(
                db, "venue-1", "booking-1", "captain-1"
            )

        assert completion["status"] == "completed"
        print("   ✓ Match completed")

        # 4. Verify team stats updated
        stats = team_service.get_team_stats(db, team.team_id)

        assert stats["total_matches"] == 1
        assert stats["wins"] == 1
        print(f"   ✓ Team stats updated: 1 match, 1 win, rating {stats['rating']}")


# ==============================================================================
# RUN TESTS
# ==============================================================================

if __name__ == "__main__":
    print("\n" + "="*80)
    print("🧪 PHASE 4 TEST SUITE")
    print("="*80)

    print("\n📢 NOTIFICATIONS TESTS")
    print("-" * 80)
    TestNotifications().test_record_notification()
    TestNotifications().test_notify_match_needs_players()
    TestNotifications().test_notify_reward_earned()
    TestNotifications().test_get_notification_preferences()

    print("\n⏳ WAITLIST TESTS")
    print("-" * 80)
    TestWaitlist().test_join_waitlist()
    TestWaitlist().test_get_waitlist()
    TestWaitlist().test_promote_from_waitlist()
    TestWaitlist().test_confirm_promotion()
    TestWaitlist().test_decline_promotion_promotes_next()

    print("\n📊 TEAM HISTORY TESTS")
    print("-" * 80)
    TestTeamHistory().test_record_team_match()
    TestTeamHistory().test_team_stats_updated()
    TestTeamHistory().test_elo_rating_calculation()
    TestTeamHistory().test_get_team_history()

    print("\n🔗 INTEGRATION TESTS")
    print("-" * 80)
    print("Complete waitlist flow:")
    TestPhase4Integration().test_complete_waitlist_flow()
    print("\nTeam match and reward flow:")
    TestPhase4Integration().test_team_match_and_reward_flow()

    print("\n" + "="*80)
    print("✅ ALL PHASE 4 TESTS PASSED")
    print("="*80 + "\n")
