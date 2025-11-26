/**
 * API client for household management
 */

import { apiRequest } from "./client";

export interface Household {
  id: number;
  name: string;
  owner_user_id: number;
  max_members: number;
  created_at: string;
  updated_at: string;
}

export interface HouseholdMember {
  id: number;
  household_id: number;
  user_id: number;
  role: "owner" | "member";
  joined_at: string;
  user_email?: string | null;
  user_display_name?: string | null;
}

export interface HouseholdInvitation {
  id: number;
  household_id: number;
  inviter_user_id: number;
  invitee_email: string;
  token: string;
  expires_at: string;
  accepted_at: string | null;
  created_at: string;
  household_name?: string | null;
  inviter_display_name?: string | null;
}

export interface CreateHouseholdRequest {
  name: string;
}

export interface UpdateHouseholdRequest {
  name: string;
}

export interface CreateInvitationRequest {
  invitee_email: string;
}

export interface AcceptInvitationRequest {
  token: string;
}

export interface HouseholdInviteLink {
  id: number;
  household_id: number;
  code: string;
  created_by_user_id: number;
  expires_at: string;
  used_at: string | null;
  used_by_user_id: number | null;
  created_at: string;
  household_name?: string | null;
  created_by_display_name?: string | null;
  used_by_display_name?: string | null;
}

export interface CreateInviteLinkRequest {
  expires_in_days?: number;
}

export interface JoinViaInviteLinkRequest {
  code: string;
}

export interface LeaveHouseholdResponse {
  message: string;
  household_deleted: boolean;
}

/**
 * Get current user's household
 */
export async function getCurrentHousehold(): Promise<Household> {
  return apiRequest<Household>("/households/me");
}

/**
 * Create a new household
 */
export async function createHousehold(
  data: CreateHouseholdRequest,
): Promise<Household> {
  return apiRequest<Household>("/households", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/**
 * Update household
 */
export async function updateHousehold(
  householdId: number,
  data: UpdateHouseholdRequest,
): Promise<Household> {
  return apiRequest<Household>(`/households/${householdId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

/**
 * Delete household
 */
export async function deleteHousehold(householdId: number): Promise<void> {
  return apiRequest<void>(`/households/${householdId}`, {
    method: "DELETE",
  });
}

/**
 * Get household members
 */
export async function getHouseholdMembers(
  householdId: number,
): Promise<HouseholdMember[]> {
  return apiRequest<HouseholdMember[]>(`/households/${householdId}/members`);
}

/**
 * Remove member from household
 */
export async function removeMember(
  householdId: number,
  userId: number,
): Promise<void> {
  return apiRequest<void>(`/households/${householdId}/members/${userId}`, {
    method: "DELETE",
  });
}

/**
 * Get household invitations
 */
export async function getHouseholdInvitations(
  householdId: number,
): Promise<HouseholdInvitation[]> {
  return apiRequest<HouseholdInvitation[]>(
    `/households/${householdId}/invitations`,
  );
}

/**
 * Create invitation
 */
export async function createInvitation(
  householdId: number,
  data: CreateInvitationRequest,
): Promise<HouseholdInvitation> {
  return apiRequest<HouseholdInvitation>(
    `/households/${householdId}/invitations`,
    {
      method: "POST",
      body: JSON.stringify(data),
    },
  );
}

/**
 * Get invitation by token (no auth required)
 */
export async function getInvitationByToken(
  token: string,
): Promise<HouseholdInvitation> {
  return apiRequest<HouseholdInvitation>(`/invitations/${token}`, {
    requireAuth: false,
  });
}

/**
 * Accept invitation
 */
export async function acceptInvitation(
  data: AcceptInvitationRequest,
): Promise<void> {
  return apiRequest<void>("/invitations/accept", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/**
 * Decline invitation
 */
export async function declineInvitation(token: string): Promise<void> {
  return apiRequest<void>("/invitations/decline", {
    method: "POST",
    body: JSON.stringify({ token }),
  });
}

/**
 * Revoke invitation (delete)
 */
export async function revokeInvitation(
  householdId: number,
  invitationId: number,
): Promise<void> {
  return apiRequest<void>(
    `/households/${householdId}/invitations/${invitationId}`,
    {
      method: "DELETE",
    },
  );
}

/**
 * Create invite link (one-time use code)
 */
export async function createInviteLink(
  householdId: number,
  data: CreateInviteLinkRequest = {},
): Promise<HouseholdInviteLink> {
  return apiRequest<HouseholdInviteLink>(
    `/households/${householdId}/invite-links`,
    {
      method: "POST",
      body: JSON.stringify(data),
    },
  );
}

/**
 * Get invite link info by code (no auth required)
 */
export async function getInviteLinkInfo(
  code: string,
): Promise<HouseholdInviteLink> {
  return apiRequest<HouseholdInviteLink>(`/households/join/${code}`, {
    requireAuth: false,
  });
}

/**
 * Join household via invite code
 */
export async function joinViaInviteLink(
  code: string,
): Promise<HouseholdMember> {
  return apiRequest<HouseholdMember>("/households/join", {
    method: "POST",
    body: JSON.stringify({ code }),
  });
}

/**
 * Leave current household
 */
export async function leaveHousehold(): Promise<LeaveHouseholdResponse> {
  return apiRequest<LeaveHouseholdResponse>("/households/leave", {
    method: "POST",
  });
}
