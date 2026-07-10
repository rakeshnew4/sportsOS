export interface MeResponse {
  uid: string;
  display_name: string | null;
  is_player: boolean;
  owner_of: string[];
  staff_of: string[];
}

export interface GeoPoint {
  lat: number;
  lng: number;
}

export interface VenueResponse {
  tenant_id: string;
  name: string;
  city: string;
  geo: GeoPoint;
  sports: string[];
}

export interface CourtResponse {
  court_id: string;
  tenant_id: string;
  name: string;
  sport: string;
  hourly_price: number;
  open_time: string;
  close_time: string;
  is_active: boolean;
  dynamic_pricing_enabled: boolean;
}

export interface SlotResponse {
  start_time: string;
  end_time: string;
  available: boolean;
  price: number | null;
}

export type BookingStatus = "pending_payment" | "confirmed" | "completed" | "cancelled";

export interface BookingResponse {
  booking_id: string;
  tenant_id: string;
  court_id: string;
  sport: string;
  date: string;
  start_time: string;
  end_time: string;
  price: number;
  status: BookingStatus;
  created_by: string;
  team_id: string | null;
  team_name: string | null;
  is_joinable: boolean;
  slots_total: number;
  slots_open: number;
}

export interface WalletResponse {
  uid: string;
  balance: number;
  currency: string;
}

export interface WalletTransactionResponse {
  tx_id: string;
  type: "credit" | "debit";
  amount: number;
  currency: string;
  reason: string;
  related_booking_id: string | null;
  balance_after: number;
  created_at: string;
}

export interface MatchResponse extends BookingResponse {
  tenant_name: string;
  geo: GeoPoint;
}

export interface ParticipantResponse {
  uid: string;
  display_name: string | null;
  joined_at: string;
}

export type MatchRequestStatus = "waiting" | "matched" | "cancelled";

export interface MatchRequestResponse {
  request_id: string;
  tenant_id: string;
  court_id: string;
  sport: string;
  date: string;
  start_time: string;
  end_time: string;
  uid: string;
  status: MatchRequestStatus;
  min_players: number;
  current_count: number;
  matched_booking_id: string | null;
}

export interface MatchCompletionResponse {
  booking_id: string;
  status: string;
  completed_at: string;
  players_checked_in: number;
  total_players: number;
  captain_rewards_earned: number;
  message: string;
}

export interface StaffMember {
  uid: string;
  display_name: string | null;
  role: string;
  added_at: string;
}

export type VenueKPIScope = "today" | "week" | "month" | "custom";

export interface RevenueMetric {
  total_revenue: number;
  transaction_count: number;
  avg_transaction_value: number;
  recurring_revenue: number;
  transaction_revenue: number;
}

export interface OccupancyMetric {
  court_id: string;
  court_name: string;
  sport: string;
  utilization_percent: number;
  booked_hours: number;
  available_hours: number;
  bookings_count: number;
  no_show_count: number;
  cancelled_count: number;
}

export interface CustomerMetric {
  active_customers: number;
  new_customers: number;
  returning_customers: number;
  repeat_booking_percent: number;
  avg_lifetime_value: number;
}

export interface TeamMetric {
  teams_formed: number;
  avg_team_size: number;
  total_team_participants: number;
  teams_completed: number;
}

export interface MatchmakingMetric {
  total_queued: number;
  matches_formed: number;
  match_fill_rate: number;
  avg_fill_time_seconds: number;
  queue_cancellations: number;
  cancellation_rate: number;
}

export interface CaptainRewardMetric {
  captain_uid: string;
  captain_name: string;
  period_start: string;
  period_end: string;
  total_credits_earned: number;
  matches_hosted: number;
  matches_with_full_slots: number;
  new_players_invited: number;
  opponent_teams_invited: number;
  opponent_teams_accepted: number;
  acceptance_rate: number;
  off_peak_matches: number;
  recurring_matches: number;
  milestone_bonuses_earned: number;
  avg_credits_per_match: number;
}

export interface MatchCompletionMetric {
  period_start: string;
  period_end: string;
  matches_created: number;
  matches_completed: number;
  completion_rate: number;
  no_show_rate: number;
  avg_actual_attendance: number;
  matches_with_disputes: number;
  dispute_rate: number;
  reward_issued_after_completion: number;
}

export interface VenueOverviewKPI {
  venue_name: string;
  scope: VenueKPIScope;
  period_start: string;
  period_end: string;
  revenue: RevenueMetric;
  occupancy: OccupancyMetric[];
  customers: CustomerMetric;
  teams: TeamMetric;
  matchmaking: MatchmakingMetric;
  captain_rewards: CaptainRewardMetric | null;
  match_completion: MatchCompletionMetric;
  avg_occupancy_percent: number;
}

export interface TeamMember {
  uid: string;
  display_name: string | null;
  joined_at: string;
}

export interface TeamResponse {
  team_id: string;
  team_name: string;
  sport: string;
  captain_uid: string;
  captain_name: string;
  status: string;
  members: TeamMember[];
  total_members: number;
  wins: number;
  losses: number;
  rating: number;
  created_at: string;
  created_by: string;
  booking_id: string | null;
}

export interface TeamCreateRequest {
  team_name: string;
  sport: string;
  description?: string;
}

export interface TeamInviteRequest {
  player_uid: string;
  player_name: string;
}

export interface TeamOpponentRequest {
  sport: string;
  date: string;
  time: string;
  venue_id?: string;
  skill_level?: string;
  match_format?: string;
  number_of_players?: number;
}

export interface TeamOpponentResponse {
  challenge_id: string;
  from_team_id: string;
  from_team_name: string;
  from_captain_uid: string;
  from_captain_name: string;
  sport: string;
  date: string;
  time: string;
  venue_id: string | null;
  skill_level: string | null;
  match_format: string | null;
  number_of_players: number;
  status: string;
  created_at: string;
}

export interface RewardRecord {
  reward_id: string;
  player_uid: string;
  reward_type: string;
  credits_amount: number;
  reason: string;
  related_booking_id: string | null;
  issued_at: string;
  status: string;
}

export interface CaptainStatsResponse {
  player_uid: string;
  player_name: string;
  matches_hosted: number;
  matches_completed: number;
  total_credits_earned: number;
  credits_this_month: number;
  new_players_invited: number;
  opponent_teams_invited: number;
  opponent_teams_accepted: number;
  acceptance_rate: number;
  off_peak_matches: number;
  recurring_matches: number;
  avg_credits_per_match: number;
  milestone_bonuses_earned: number;
  last_match_date: string | null;
}

export interface CaptainLeaderboardEntry {
  rank: number;
  player_uid: string;
  player_name: string;
  credits_earned_month: number;
  matches_hosted_month: number;
  new_players_brought: number;
  acceptance_rate: number;
}

export interface ReferralTracking {
  referral_id: string;
  referrer_uid: string;
  referred_player_uid: string;
  referred_player_name: string;
  referred_at: string;
  first_match_date: string | null;
  credits_earned: number;
  referrer_ltv: number | null;
}

export interface WaitlistEntry {
  player_uid: string;
  position: number;
  joined_at: string;
  status: string;
}

export interface WaitlistResponse {
  booking_id: string;
  total_waiting: number;
  queue: WaitlistEntry[];
}

export interface MyWaitlistPosition {
  booking_id: string;
  player_uid: string;
  position: number;
  status: string;
  joined_at: string;
}

export interface JoinWaitlistResponse {
  success: boolean;
  booking_id: string;
  position: number;
  message: string;
}

export interface NotificationResponse {
  notification_id: string;
  type: string;
  title: string;
  body: string;
  data: Record<string, unknown>;
  created_at: string;
  read_at: string | null;
  clicked_at: string | null;
}

export interface NotificationPreferences {
  match_needs_players: boolean;
  team_challenge: boolean;
  match_reminder: boolean;
  reward_earned: boolean;
  promoted_from_waitlist: boolean;
  frequency: string;
  quiet_hours_start: string | null;
  quiet_hours_end: string | null;
}

export interface InviteCandidate {
  uid: string;
  display_name: string;
  tier: "playmate" | "queue" | "nearby";
  reason: string;
}

export interface MatchInviteResponse {
  invite_id: string;
  booking_id: string;
  from_uid: string;
  to_uid: string;
  tier: string;
  status: "pending" | "accepted" | "declined" | "expired";
  title: string;
  body: string;
  created_at: string;
}

export interface InvitePreferences {
  open_to_invites: boolean;
  radius_km: number;
  preferred_court_ids: string[];
}

export interface RatingCreate {
  rated_uid: string;
  booking_id: string;
  rating: number;
  comment?: string;
}

export interface RatingResponse {
  rating_id: string;
  from_uid: string;
  to_uid: string;
  booking_id: string;
  rating: number;
  comment: string;
  created_at: string;
}

export interface PlayerRatingsStats {
  uid: string;
  avg_rating: number;
  total_ratings: number;
  rating_distribution: Record<number, number>;
}

export interface PlayerEngagementKPI {
  uid: string;
  display_name: string | null;
  scope: string;
  period_start: string;
  period_end: string;
  matches_played: number;
  teams_captained: number;
  teams_joined: number;
  courts_booked: number;
  hours_played: number;
  bookings_this_period: number;
  wallet_total_spend: number;
  wallet_balance: number;
  credits_earned: number;
  credits_redeemed: number;
  credits_outstanding: number;
  weekly_sessions: number;
  favorite_venue: string | null;
  favorite_sport: string | null;
  repeat_venues: number;
  players_referred: number;
  is_captain: boolean;
  is_active_captain: boolean;
}
