/**
 * Session-level cache for bank configurations
 * Reduces API calls and improves user experience
 */

import { apiService, type BankConfiguration } from './api'

interface BankCache {
  data: BankConfiguration[]
  timestamp: number
  isLoading: boolean
}

class BankCacheService {
  private cache: BankCache | null = null
  private readonly CACHE_DURATION = 5 * 60 * 1000 // 5 minutes
  private fetchPromise: Promise<BankConfiguration[]> | null = null

  /**
   * Get banks with caching strategy
   * Returns cached data if available and not expired
   */
  async getBanks(): Promise<BankConfiguration[]> {
    // Return cached data if valid
    if (this.isCacheValid()) {
      return this.cache!.data
    }

    // If already fetching, return the existing promise
    if (this.fetchPromise) {
      return this.fetchPromise
    }

    // Fetch fresh data
    this.fetchPromise = this.fetchFreshBanks()

    try {
      const banks = await this.fetchPromise
      this.updateCache(banks)
      return banks
    } finally {
      this.fetchPromise = null
    }
  }

  /**
   * Check if we have valid cached data
   */
  private isCacheValid(): boolean {
    if (!this.cache) return false

    const now = Date.now()
    const isExpired = now - this.cache.timestamp > this.CACHE_DURATION

    return !isExpired && this.cache.data.length > 0
  }

  /**
   * Fetch banks from API
   */
  private async fetchFreshBanks(): Promise<BankConfiguration[]> {
    const response = await apiService.getBankConfigurations()
    return response.data || []
  }

  /**
   * Update cache with fresh data
   */
  private updateCache(banks: BankConfiguration[]): void {
    this.cache = {
      data: banks,
      timestamp: Date.now(),
      isLoading: false
    }
  }

  /**
   * Clear cache (useful for manual refresh)
   */
  clearCache(): void {
    this.cache = null
    this.fetchPromise = null
  }

  /**
   * Get cached data without fetching (for immediate UI updates)
   */
  getCachedBanks(): BankConfiguration[] {
    return this.cache?.data || []
  }

  /**
   * Check if currently fetching
   */
  isLoading(): boolean {
    return this.fetchPromise !== null
  }
}

// Export singleton instance
export const bankCache = new BankCacheService()