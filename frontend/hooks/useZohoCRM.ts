/**
 * React Hooks for Zoho CRM Integration
 * Provides data fetching and management for Zoho leads, contacts, accounts, and activities
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { apiClient } from '@/lib/api';

// Zoho CRM data types
interface ZohoLead {
  id: string
  firstName: string
  lastName: string
  email: string
  phone?: string
  mobile?: string
  company?: string
  designation?: string
  leadSource: string
  leadStatus: string
  rating: 'Hot' | 'Warm' | 'Cold'
  leadScore?: number
  street?: string
  city?: string
  state?: string
  zipCode?: string
  country?: string
  website?: string
  industry?: string
  annualRevenue?: number
  employees?: number
  description?: string
  tags?: string[]
  createdTime: string
  modifiedTime: string
  owner: {
    name: string
    email: string
    id: string
  }
  customFields?: Record<string, any>
}

interface ZohoContact {
  id: string
  firstName: string
  lastName: string
  email: string
  phone?: string
  mobile?: string
  title?: string
  department?: string
  mailingStreet?: string
  mailingCity?: string
  mailingState?: string
  mailingZip?: string
  mailingCountry?: string
  accountName?: string
  leadSource?: string
  contactOwner: {
    name: string
    email: string
    id: string
  }
  createdTime: string
  modifiedTime: string
  tags?: string[]
  customFields?: Record<string, any>
}

interface ZohoAccount {
  id: string
  accountName: string
  website?: string
  phone?: string
  industry?: string
  type?: string
  annualRevenue?: number
  employees?: number
  billingStreet?: string
  billingCity?: string
  billingState?: string
  billingZip?: string
  billingCountry?: string
  description?: string
  accountOwner: {
    name: string
    email: string
    id: string
  }
  createdTime: string
  modifiedTime: string
  tags?: string[]
  customFields?: Record<string, any>
}

interface ZohoActivity {
  id: string
  subject: string
  activityType: 'Call' | 'Meeting' | 'Email' | 'Task' | 'Event'
  status: 'Not Started' | 'In Progress' | 'Completed' | 'Cancelled'
  priority: 'High' | 'Medium' | 'Low'
  dueDate?: string
  startDateTime?: string
  endDateTime?: string
  description?: string
  relatedTo: {
    module: 'Leads' | 'Contacts' | 'Accounts'
    id: string
    name: string
  }
  owner: {
    name: string
    email: string
    id: string
  }
  createdTime: string
  modifiedTime: string
}

interface SearchFilters {
  query?: string
  leadStatus?: string[]
  rating?: string[]
  leadSource?: string[]
  industry?: string[]
  owner?: string
  dateRange?: {
    from: string
    to: string
  }
  tags?: string[]
}

interface UseZohoLeadsReturn {
  leads: ZohoLead[]
  isLoading: boolean
  error: string | null
  totalCount: number
  hasMore: boolean
  searchLeads: (filters: SearchFilters) => Promise<void>
  loadMore: () => Promise<void>
  refreshLeads: () => Promise<void>
  createLead: (leadData: Partial<ZohoLead>) => Promise<ZohoLead>
  updateLead: (id: string, updates: Partial<ZohoLead>) => Promise<ZohoLead>
  convertLead: (id: string, options: { createContact: boolean; createAccount: boolean; createDeal: boolean }) => Promise<any>
}

interface UseZohoContactsReturn {
  contacts: ZohoContact[]
  isLoading: boolean
  error: string | null
  totalCount: number
  hasMore: boolean
  searchContacts: (filters: SearchFilters) => Promise<void>
  loadMore: () => Promise<void>
  refreshContacts: () => Promise<void>
  createContact: (contactData: Partial<ZohoContact>) => Promise<ZohoContact>
  updateContact: (id: string, updates: Partial<ZohoContact>) => Promise<ZohoContact>
}

interface UseZohoAccountsReturn {
  accounts: ZohoAccount[]
  isLoading: boolean
  error: string | null
  totalCount: number
  hasMore: boolean
  searchAccounts: (filters: SearchFilters) => Promise<void>
  loadMore: () => Promise<void>
  refreshAccounts: () => Promise<void>
  createAccount: (accountData: Partial<ZohoAccount>) => Promise<ZohoAccount>
  updateAccount: (id: string, updates: Partial<ZohoAccount>) => Promise<ZohoAccount>
}

interface UseZohoActivitiesReturn {
  activities: ZohoActivity[]
  isLoading: boolean
  error: string | null
  getActivitiesForRecord: (module: 'Leads' | 'Contacts' | 'Accounts', recordId: string) => Promise<void>
  createActivity: (activityData: Partial<ZohoActivity>) => Promise<ZohoActivity>
  updateActivity: (id: string, updates: Partial<ZohoActivity>) => Promise<ZohoActivity>
  deleteActivity: (id: string) => Promise<void>
  refreshActivities: () => Promise<void>
}

// Zoho API client
class ZohoApi {
  constructor(private apiClient: any) {}

  // Leads
  async searchLeads(filters: SearchFilters, page = 1, perPage = 50): Promise<{ data: ZohoLead[], totalCount: number, hasMore: boolean }> {
    const params = new URLSearchParams({
      page: page.toString(),
      per_page: perPage.toString(),
      ...filters.query && { query: filters.query },
      ...filters.leadStatus && { lead_status: filters.leadStatus.join(',') },
      ...filters.rating && { rating: filters.rating.join(',') },
      ...filters.leadSource && { lead_source: filters.leadSource.join(',') },
      ...filters.industry && { industry: filters.industry.join(',') },
      ...filters.owner && { owner: filters.owner },
      ...filters.tags && { tags: filters.tags.join(',') },
      ...filters.dateRange && {
        date_from: filters.dateRange.from,
        date_to: filters.dateRange.to
      }
    });

    const response = await this.apiClient.get(`/api/crm/leads?${params}`);
    return response.data;
  }

  async createLead(leadData: Partial<ZohoLead>): Promise<ZohoLead> {
    const response = await this.apiClient.post('/api/crm/leads', leadData);
    return response.data;
  }

  async updateLead(id: string, updates: Partial<ZohoLead>): Promise<ZohoLead> {
    const response = await this.apiClient.put(`/api/crm/leads/${id}`, updates);
    return response.data;
  }

  async convertLead(id: string, options: { createContact: boolean; createAccount: boolean; createDeal: boolean }): Promise<any> {
    const response = await this.apiClient.post(`/api/crm/leads/${id}/convert`, options);
    return response.data;
  }

  // Contacts
  async searchContacts(filters: SearchFilters, page = 1, perPage = 50): Promise<{ data: ZohoContact[], totalCount: number, hasMore: boolean }> {
    const params = new URLSearchParams({
      page: page.toString(),
      per_page: perPage.toString(),
      ...filters.query && { query: filters.query },
      ...filters.owner && { owner: filters.owner },
      ...filters.tags && { tags: filters.tags.join(',') },
      ...filters.dateRange && {
        date_from: filters.dateRange.from,
        date_to: filters.dateRange.to
      }
    });

    const response = await this.apiClient.get(`/api/crm/contacts?${params}`);
    return response.data;
  }

  async createContact(contactData: Partial<ZohoContact>): Promise<ZohoContact> {
    const response = await this.apiClient.post('/api/crm/contacts', contactData);
    return response.data;
  }

  async updateContact(id: string, updates: Partial<ZohoContact>): Promise<ZohoContact> {
    const response = await this.apiClient.put(`/api/crm/contacts/${id}`, updates);
    return response.data;
  }

  // Accounts
  async searchAccounts(filters: SearchFilters, page = 1, perPage = 50): Promise<{ data: ZohoAccount[], totalCount: number, hasMore: boolean }> {
    const params = new URLSearchParams({
      page: page.toString(),
      per_page: perPage.toString(),
      ...filters.query && { query: filters.query },
      ...filters.industry && { industry: filters.industry.join(',') },
      ...filters.owner && { owner: filters.owner },
      ...filters.tags && { tags: filters.tags.join(',') },
      ...filters.dateRange && {
        date_from: filters.dateRange.from,
        date_to: filters.dateRange.to
      }
    });

    const response = await this.apiClient.get(`/api/crm/accounts?${params}`);
    return response.data;
  }

  async createAccount(accountData: Partial<ZohoAccount>): Promise<ZohoAccount> {
    const response = await this.apiClient.post('/api/crm/accounts', accountData);
    return response.data;
  }

  async updateAccount(id: string, updates: Partial<ZohoAccount>): Promise<ZohoAccount> {
    const response = await this.apiClient.put(`/api/crm/accounts/${id}`, updates);
    return response.data;
  }

  // Activities
  async getActivitiesForRecord(module: 'Leads' | 'Contacts' | 'Accounts', recordId: string): Promise<ZohoActivity[]> {
    const response = await this.apiClient.get(`/api/crm/activities?module=${module}&record_id=${recordId}`);
    return response.data;
  }

  async createActivity(activityData: Partial<ZohoActivity>): Promise<ZohoActivity> {
    const response = await this.apiClient.post('/api/crm/activities', activityData);
    return response.data;
  }

  async updateActivity(id: string, updates: Partial<ZohoActivity>): Promise<ZohoActivity> {
    const response = await this.apiClient.put(`/api/crm/activities/${id}`, updates);
    return response.data;
  }

  async deleteActivity(id: string): Promise<void> {
    await this.apiClient.delete(`/api/crm/activities/${id}`);
  }
}

// Hooks implementation
export const useZohoLeads = (initialFilters?: SearchFilters): UseZohoLeadsReturn => {
  const [leads, setLeads] = useState<ZohoLead[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [totalCount, setTotalCount] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [currentFilters, setCurrentFilters] = useState<SearchFilters>(initialFilters || {});

  const zohoApi = new ZohoApi(apiClient);

  const searchLeads = useCallback(async (filters: SearchFilters) => {
    try {
      setIsLoading(true);
      setError(null);
      setCurrentFilters(filters);
      setCurrentPage(1);

      const result = await zohoApi.searchLeads(filters, 1, 50);
      setLeads(result.data);
      setTotalCount(result.totalCount);
      setHasMore(result.hasMore);
    } catch (err: any) {
      setError(err.message || 'Failed to search leads');
    } finally {
      setIsLoading(false);
    }
  }, [zohoApi]);

  const loadMore = useCallback(async () => {
    if (!hasMore || isLoading) return;

    try {
      setIsLoading(true);
      const nextPage = currentPage + 1;
      const result = await zohoApi.searchLeads(currentFilters, nextPage, 50);

      setLeads(prev => [...prev, ...result.data]);
      setCurrentPage(nextPage);
      setHasMore(result.hasMore);
    } catch (err: any) {
      setError(err.message || 'Failed to load more leads');
    } finally {
      setIsLoading(false);
    }
  }, [hasMore, isLoading, currentPage, currentFilters, zohoApi]);

  const refreshLeads = useCallback(async () => {
    await searchLeads(currentFilters);
  }, [searchLeads, currentFilters]);

  const createLead = useCallback(async (leadData: Partial<ZohoLead>) => {
    try {
      setIsLoading(true);
      const newLead = await zohoApi.createLead(leadData);
      setLeads(prev => [newLead, ...prev]);
      setTotalCount(prev => prev + 1);
      return newLead;
    } catch (err: any) {
      setError(err.message || 'Failed to create lead');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [zohoApi]);

  const updateLead = useCallback(async (id: string, updates: Partial<ZohoLead>) => {
    try {
      setIsLoading(true);
      const updatedLead = await zohoApi.updateLead(id, updates);
      setLeads(prev => prev.map(lead => lead.id === id ? updatedLead : lead));
      return updatedLead;
    } catch (err: any) {
      setError(err.message || 'Failed to update lead');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [zohoApi]);

  const convertLead = useCallback(async (id: string, options: { createContact: boolean; createAccount: boolean; createDeal: boolean }) => {
    try {
      setIsLoading(true);
      const result = await zohoApi.convertLead(id, options);
      // Remove converted lead from list
      setLeads(prev => prev.filter(lead => lead.id !== id));
      setTotalCount(prev => prev - 1);
      return result;
    } catch (err: any) {
      setError(err.message || 'Failed to convert lead');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [zohoApi]);

  // Initial load
  useEffect(() => {
    if (initialFilters) {
      searchLeads(initialFilters);
    }
  }, []);

  return {
    leads,
    isLoading,
    error,
    totalCount,
    hasMore,
    searchLeads,
    loadMore,
    refreshLeads,
    createLead,
    updateLead,
    convertLead
  };
};

export const useZohoContacts = (initialFilters?: SearchFilters): UseZohoContactsReturn => {
  const [contacts, setContacts] = useState<ZohoContact[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [totalCount, setTotalCount] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [currentFilters, setCurrentFilters] = useState<SearchFilters>(initialFilters || {});

  const zohoApi = new ZohoApi(apiClient);

  const searchContacts = useCallback(async (filters: SearchFilters) => {
    try {
      setIsLoading(true);
      setError(null);
      setCurrentFilters(filters);
      setCurrentPage(1);

      const result = await zohoApi.searchContacts(filters, 1, 50);
      setContacts(result.data);
      setTotalCount(result.totalCount);
      setHasMore(result.hasMore);
    } catch (err: any) {
      setError(err.message || 'Failed to search contacts');
    } finally {
      setIsLoading(false);
    }
  }, [zohoApi]);

  const loadMore = useCallback(async () => {
    if (!hasMore || isLoading) return;

    try {
      setIsLoading(true);
      const nextPage = currentPage + 1;
      const result = await zohoApi.searchContacts(currentFilters, nextPage, 50);

      setContacts(prev => [...prev, ...result.data]);
      setCurrentPage(nextPage);
      setHasMore(result.hasMore);
    } catch (err: any) {
      setError(err.message || 'Failed to load more contacts');
    } finally {
      setIsLoading(false);
    }
  }, [hasMore, isLoading, currentPage, currentFilters, zohoApi]);

  const refreshContacts = useCallback(async () => {
    await searchContacts(currentFilters);
  }, [searchContacts, currentFilters]);

  const createContact = useCallback(async (contactData: Partial<ZohoContact>) => {
    try {
      setIsLoading(true);
      const newContact = await zohoApi.createContact(contactData);
      setContacts(prev => [newContact, ...prev]);
      setTotalCount(prev => prev + 1);
      return newContact;
    } catch (err: any) {
      setError(err.message || 'Failed to create contact');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [zohoApi]);

  const updateContact = useCallback(async (id: string, updates: Partial<ZohoContact>) => {
    try {
      setIsLoading(true);
      const updatedContact = await zohoApi.updateContact(id, updates);
      setContacts(prev => prev.map(contact => contact.id === id ? updatedContact : contact));
      return updatedContact;
    } catch (err: any) {
      setError(err.message || 'Failed to update contact');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [zohoApi]);

  useEffect(() => {
    if (initialFilters) {
      searchContacts(initialFilters);
    }
  }, []);

  return {
    contacts,
    isLoading,
    error,
    totalCount,
    hasMore,
    searchContacts,
    loadMore,
    refreshContacts,
    createContact,
    updateContact
  };
};

export const useZohoAccounts = (initialFilters?: SearchFilters): UseZohoAccountsReturn => {
  const [accounts, setAccounts] = useState<ZohoAccount[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [totalCount, setTotalCount] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [currentFilters, setCurrentFilters] = useState<SearchFilters>(initialFilters || {});

  const zohoApi = new ZohoApi(apiClient);

  const searchAccounts = useCallback(async (filters: SearchFilters) => {
    try {
      setIsLoading(true);
      setError(null);
      setCurrentFilters(filters);
      setCurrentPage(1);

      const result = await zohoApi.searchAccounts(filters, 1, 50);
      setAccounts(result.data);
      setTotalCount(result.totalCount);
      setHasMore(result.hasMore);
    } catch (err: any) {
      setError(err.message || 'Failed to search accounts');
    } finally {
      setIsLoading(false);
    }
  }, [zohoApi]);

  const loadMore = useCallback(async () => {
    if (!hasMore || isLoading) return;

    try {
      setIsLoading(true);
      const nextPage = currentPage + 1;
      const result = await zohoApi.searchAccounts(currentFilters, nextPage, 50);

      setAccounts(prev => [...prev, ...result.data]);
      setCurrentPage(nextPage);
      setHasMore(result.hasMore);
    } catch (err: any) {
      setError(err.message || 'Failed to load more accounts');
    } finally {
      setIsLoading(false);
    }
  }, [hasMore, isLoading, currentPage, currentFilters, zohoApi]);

  const refreshAccounts = useCallback(async () => {
    await searchAccounts(currentFilters);
  }, [searchAccounts, currentFilters]);

  const createAccount = useCallback(async (accountData: Partial<ZohoAccount>) => {
    try {
      setIsLoading(true);
      const newAccount = await zohoApi.createAccount(accountData);
      setAccounts(prev => [newAccount, ...prev]);
      setTotalCount(prev => prev + 1);
      return newAccount;
    } catch (err: any) {
      setError(err.message || 'Failed to create account');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [zohoApi]);

  const updateAccount = useCallback(async (id: string, updates: Partial<ZohoAccount>) => {
    try {
      setIsLoading(true);
      const updatedAccount = await zohoApi.updateAccount(id, updates);
      setAccounts(prev => prev.map(account => account.id === id ? updatedAccount : account));
      return updatedAccount;
    } catch (err: any) {
      setError(err.message || 'Failed to update account');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [zohoApi]);

  useEffect(() => {
    if (initialFilters) {
      searchAccounts(initialFilters);
    }
  }, []);

  return {
    accounts,
    isLoading,
    error,
    totalCount,
    hasMore,
    searchAccounts,
    loadMore,
    refreshAccounts,
    createAccount,
    updateAccount
  };
};

export const useZohoActivities = (recordModule?: 'Leads' | 'Contacts' | 'Accounts', recordId?: string): UseZohoActivitiesReturn => {
  const [activities, setActivities] = useState<ZohoActivity[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const zohoApi = new ZohoApi(apiClient);

  const getActivitiesForRecord = useCallback(async (module: 'Leads' | 'Contacts' | 'Accounts', recordId: string) => {
    try {
      setIsLoading(true);
      setError(null);
      const data = await zohoApi.getActivitiesForRecord(module, recordId);
      setActivities(data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch activities');
    } finally {
      setIsLoading(false);
    }
  }, [zohoApi]);

  const createActivity = useCallback(async (activityData: Partial<ZohoActivity>) => {
    try {
      setIsLoading(true);
      const newActivity = await zohoApi.createActivity(activityData);
      setActivities(prev => [newActivity, ...prev]);
      return newActivity;
    } catch (err: any) {
      setError(err.message || 'Failed to create activity');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [zohoApi]);

  const updateActivity = useCallback(async (id: string, updates: Partial<ZohoActivity>) => {
    try {
      setIsLoading(true);
      const updatedActivity = await zohoApi.updateActivity(id, updates);
      setActivities(prev => prev.map(activity => activity.id === id ? updatedActivity : activity));
      return updatedActivity;
    } catch (err: any) {
      setError(err.message || 'Failed to update activity');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [zohoApi]);

  const deleteActivity = useCallback(async (id: string) => {
    try {
      setIsLoading(true);
      await zohoApi.deleteActivity(id);
      setActivities(prev => prev.filter(activity => activity.id !== id));
    } catch (err: any) {
      setError(err.message || 'Failed to delete activity');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [zohoApi]);

  const refreshActivities = useCallback(async () => {
    if (recordModule && recordId) {
      await getActivitiesForRecord(recordModule, recordId);
    }
  }, [getActivitiesForRecord, recordModule, recordId]);

  useEffect(() => {
    if (recordModule && recordId) {
      getActivitiesForRecord(recordModule, recordId);
    }
  }, [recordModule, recordId, getActivitiesForRecord]);

  return {
    activities,
    isLoading,
    error,
    getActivitiesForRecord,
    createActivity,
    updateActivity,
    deleteActivity,
    refreshActivities
  };
};