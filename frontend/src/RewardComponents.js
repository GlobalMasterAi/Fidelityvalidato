import React, { useState } from 'react';

// Sub-componenti per la gestione premi per evitare un file App.js troppo grande

export const RewardsList = ({ rewards, total, page, onPageChange, filters, onFiltersChange, onEdit, onDelete, getStatusColor, getCategoryColor, loading }) => {
  const rewardCategories = ['Sconti', 'Omaggi', 'VIP', 'Buoni', 'Servizi', 'Eventi', 'Speciali'];

  const handleFilterChange = (key, value) => {
    onFiltersChange({ ...filters, [key]: value });
  };

  const formatValue = (reward) => {
    if (reward.type === 'discount_percentage') {
      return `${reward.discount_percentage}%`;
    } else if (reward.type === 'discount_fixed' || reward.type === 'voucher') {
      return `€${reward.discount_amount}`;
    } else if (reward.type === 'free_product') {
      return reward.product_sku || 'Prodotto gratuito';
    }
    return 'Personalizzato';
  };

  const formatExpiry = (reward) => {
    if (reward.expiry_type === 'fixed_date' && reward.expiry_date) {
      return new Date(reward.expiry_date).toLocaleDateString('it-IT');
    } else if (reward.expiry_type === 'days_from_creation' && reward.expiry_days_from_creation) {
      return `${reward.expiry_days_from_creation} giorni dalla creazione`;
    } else if (reward.expiry_type === 'days_from_redemption' && reward.expiry_days_from_redemption) {
      return `${reward.expiry_days_from_redemption} giorni dal riscatto`;
    }
    return 'Non specificato';
  };

  const totalPages = Math.ceil(total / 10);

  return (
    <div className="space-y-6">
      {/* Filters */}
      <div className="bg-white rounded-lg p-6 shadow-sm border">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Filtri</h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Cerca</label>
            <input
              type="text"
              value={filters.search}
              onChange={(e) => handleFilterChange('search', e.target.value)}
              placeholder="Titolo o descrizione..."
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-imagross-orange focus:border-transparent"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Stato</label>
            <select
              value={filters.status}
              onChange={(e) => handleFilterChange('status', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-imagross-orange focus:border-transparent"
            >
              <option value="">Tutti gli stati</option>
              <option value="active">Attivo</option>
              <option value="inactive">Inattivo</option>
              <option value="expired">Scaduto</option>
              <option value="out_of_stock">Esaurito</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Categoria</label>
            <select
              value={filters.category}
              onChange={(e) => handleFilterChange('category', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-imagross-orange focus:border-transparent"
            >
              <option value="">Tutte le categorie</option>
              {rewardCategories.map(cat => (
                <option key={cat} value={cat}>{cat}</option>
              ))}
            </select>
          </div>
          
          <div className="flex items-end">
            <button
              onClick={() => onFiltersChange({ search: '', status: '', category: '' })}
              className="px-4 py-2 text-sm bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 transition-colors"
            >
              Pulisci Filtri
            </button>
          </div>
        </div>
      </div>

      {/* Rewards Table */}
      <div className="bg-white rounded-lg shadow-sm border overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">
            Premi ({total})
          </h3>
        </div>

        {loading ? (
          <div className="p-6">
            <div className="animate-pulse space-y-4">
              {Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="flex space-x-4">
                  <div className="h-4 bg-gray-200 rounded w-1/4"></div>
                  <div className="h-4 bg-gray-200 rounded w-1/6"></div>
                  <div className="h-4 bg-gray-200 rounded w-1/6"></div>
                  <div className="h-4 bg-gray-200 rounded w-1/4"></div>
                  <div className="h-4 bg-gray-200 rounded w-1/6"></div>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Premio</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Categoria</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Valore</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Bollini</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Stock</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Stato</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Scadenza</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Azioni</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {rewards.map((reward) => (
                    <tr key={reward.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center space-x-3">
                          <span className="text-2xl">{reward.icon}</span>
                          <div>
                            <div className="text-sm font-medium text-gray-900">{reward.title}</div>
                            <div className="text-sm text-gray-500 truncate max-w-xs">{reward.description}</div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 py-1 text-xs font-medium rounded-full ${getCategoryColor(reward.category)}`}>
                          {reward.category}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {formatValue(reward)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-purple-600">{reward.bollini_required}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {reward.total_stock ? `${reward.remaining_stock || 0}/${reward.total_stock}` : '∞'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(reward.status)}`}>
                          {reward.status === 'active' ? 'Attivo' : 
                           reward.status === 'inactive' ? 'Inattivo' :
                           reward.status === 'expired' ? 'Scaduto' : 'Esaurito'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {formatExpiry(reward)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <div className="flex space-x-2">
                          <button
                            onClick={() => onEdit(reward)}
                            className="text-imagross-orange hover:text-imagross-red"
                          >
                            Modifica
                          </button>
                          <button
                            onClick={() => onDelete(reward.id)}
                            className="text-red-600 hover:text-red-900"
                          >
                            Disattiva
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {rewards.length === 0 && (
              <div className="text-center py-12">
                <div className="text-6xl mb-4">🎁</div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Nessun premio trovato</h3>
                <p className="text-gray-600">Crea il primo premio per iniziare.</p>
              </div>
            )}

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="px-6 py-4 border-t border-gray-200">
                <div className="flex items-center justify-between">
                  <div className="text-sm text-gray-700">
                    Pagina {page} di {totalPages} ({total} premi totali)
                  </div>
                  <div className="flex space-x-2">
                    <button
                      onClick={() => onPageChange(page - 1)}
                      disabled={page === 1}
                      className="px-3 py-1 text-sm bg-gray-200 text-gray-700 rounded disabled:opacity-50 hover:bg-gray-300 transition-colors"
                    >
                      Precedente
                    </button>
                    <button
                      onClick={() => onPageChange(page + 1)}
                      disabled={page === totalPages}
                      className="px-3 py-1 text-sm bg-gray-200 text-gray-700 rounded disabled:opacity-50 hover:bg-gray-300 transition-colors"
                    >
                      Successivo
                    </button>
                  </div>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export const RedemptionsList = ({ redemptions, total, page, onPageChange, filters, onFiltersChange, onProcess, onMarkUsed, getStatusColor, loading }) => {
  const handleFilterChange = (key, value) => {
    onFiltersChange({ ...filters, [key]: value });
  };

  const totalPages = Math.ceil(total / 10);

  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleDateString('it-IT', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="space-y-6">
      {/* Filters */}
      <div className="bg-white rounded-lg p-6 shadow-sm border">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Filtri Riscatti</h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Stato</label>
            <select
              value={filters.status}
              onChange={(e) => handleFilterChange('status', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-imagross-orange focus:border-transparent"
            >
              <option value="">Tutti gli stati</option>
              <option value="pending">In Attesa</option>
              <option value="approved">Approvato</option>
              <option value="used">Utilizzato</option>
              <option value="rejected">Rifiutato</option>
              <option value="expired">Scaduto</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Data Da</label>
            <input
              type="date"
              value={filters.date_from}
              onChange={(e) => handleFilterChange('date_from', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-imagross-orange focus:border-transparent"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Data A</label>
            <input
              type="date"
              value={filters.date_to}
              onChange={(e) => handleFilterChange('date_to', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-imagross-orange focus:border-transparent"
            />
          </div>
          
          <div className="flex items-end">
            <button
              onClick={() => onFiltersChange({ status: '', reward_id: '', date_from: '', date_to: '' })}
              className="px-4 py-2 text-sm bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 transition-colors"
            >
              Pulisci Filtri
            </button>
          </div>
        </div>
      </div>

      {/* Redemptions Table */}
      <div className="bg-white rounded-lg shadow-sm border overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">
            Riscatti ({total})
          </h3>
        </div>

        {loading ? (
          <div className="p-6">
            <div className="animate-pulse space-y-4">
              {Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="flex space-x-4">
                  <div className="h-4 bg-gray-200 rounded w-1/4"></div>
                  <div className="h-4 bg-gray-200 rounded w-1/6"></div>
                  <div className="h-4 bg-gray-200 rounded w-1/6"></div>
                  <div className="h-4 bg-gray-200 rounded w-1/4"></div>
                  <div className="h-4 bg-gray-200 rounded w-1/6"></div>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Codice</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Premio</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Utente</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Data</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Stato</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Scadenza</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Azioni</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {redemptions.map((redemption) => (
                    <tr key={redemption.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-mono font-medium text-imagross-orange">
                          {redemption.redemption_code}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">
                          {redemption.reward_info?.title || 'Premio'}
                        </div>
                        <div className="text-sm text-gray-500">
                          {redemption.reward_info?.category}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">
                          {redemption.user_info?.nome} {redemption.user_info?.cognome}
                        </div>
                        <div className="text-sm text-gray-500">
                          {redemption.user_info?.tessera_fisica}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {formatDate(redemption.redeemed_at)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(redemption.status)}`}>
                          {redemption.status === 'pending' ? 'In Attesa' :
                           redemption.status === 'approved' ? 'Approvato' :
                           redemption.status === 'used' ? 'Utilizzato' :
                           redemption.status === 'rejected' ? 'Rifiutato' : 'Scaduto'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {redemption.expires_at ? formatDate(redemption.expires_at) : 'Mai'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <div className="flex space-x-2">
                          {redemption.status === 'pending' && (
                            <button
                              onClick={() => onProcess(redemption)}
                              className="text-imagross-orange hover:text-imagross-red"
                            >
                              Gestisci
                            </button>
                          )}
                          {redemption.status === 'approved' && redemption.uses_remaining > 0 && (
                            <button
                              onClick={() => onMarkUsed(redemption.id, {})}
                              className="text-green-600 hover:text-green-900"
                            >
                              Segna Usato
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {redemptions.length === 0 && (
              <div className="text-center py-12">
                <div className="text-6xl mb-4">🎫</div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Nessun riscatto trovato</h3>
                <p className="text-gray-600">I riscatti appariranno qui quando gli utenti riscatteranno premi.</p>
              </div>
            )}

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="px-6 py-4 border-t border-gray-200">
                <div className="flex items-center justify-between">
                  <div className="text-sm text-gray-700">
                    Pagina {page} di {totalPages} ({total} riscatti totali)
                  </div>
                  <div className="flex space-x-2">
                    <button
                      onClick={() => onPageChange(page - 1)}
                      disabled={page === 1}
                      className="px-3 py-1 text-sm bg-gray-200 text-gray-700 rounded disabled:opacity-50 hover:bg-gray-300 transition-colors"
                    >
                      Precedente
                    </button>
                    <button
                      onClick={() => onPageChange(page + 1)}
                      disabled={page === totalPages}
                      className="px-3 py-1 text-sm bg-gray-200 text-gray-700 rounded disabled:opacity-50 hover:bg-gray-300 transition-colors"
                    >
                      Successivo
                    </button>
                  </div>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export const RewardAnalytics = ({ analytics, loading }) => {
  if (loading || !analytics) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="bg-white rounded-lg p-6 shadow-sm border animate-pulse">
              <div className="h-4 bg-gray-200 rounded w-1/2 mb-2"></div>
              <div className="h-8 bg-gray-200 rounded w-1/3"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  const { overview, time_series, status_breakdown, popular_rewards, category_stats } = analytics;

  return (
    <div className="space-y-6">
      {/* Overview Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-gradient-to-r from-indigo-500 to-indigo-600 rounded-lg p-6 text-white">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm opacity-90">Tasso Conversione</div>
              <div className="text-3xl font-bold">
                {overview.total_rewards > 0 ? Math.round((overview.total_redemptions / overview.total_rewards) * 100) : 0}%
              </div>
            </div>
            <div className="text-4xl opacity-75">📈</div>
          </div>
        </div>

        <div className="bg-gradient-to-r from-teal-500 to-teal-600 rounded-lg p-6 text-white">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm opacity-90">Ultimi 30 Giorni</div>
              <div className="text-3xl font-bold">{time_series?.total_last_30_days || 0}</div>
            </div>
            <div className="text-4xl opacity-75">📅</div>
          </div>
        </div>

        <div className="bg-gradient-to-r from-orange-500 to-orange-600 rounded-lg p-6 text-white">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm opacity-90">In Lavorazione</div>
              <div className="text-3xl font-bold">{(status_breakdown?.pending || 0) + (status_breakdown?.approved || 0)}</div>
            </div>
            <div className="text-4xl opacity-75">⚙️</div>
          </div>
        </div>

        <div className="bg-gradient-to-r from-pink-500 to-pink-600 rounded-lg p-6 text-white">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm opacity-90">Completati</div>
              <div className="text-3xl font-bold">{status_breakdown?.used || 0}</div>
            </div>
            <div className="text-4xl opacity-75">✅</div>
          </div>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Status Breakdown */}
        <div className="bg-white rounded-lg p-6 shadow-sm border">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Stato Riscatti</h3>
          <div className="space-y-3">
            {Object.entries(status_breakdown || {}).map(([status, count]) => (
              <div key={status} className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <div className="w-3 h-3 rounded-full bg-imagross-orange"></div>
                  <span className="text-sm font-medium text-gray-700 capitalize">
                    {status === 'pending' ? 'In Attesa' :
                     status === 'approved' ? 'Approvato' :
                     status === 'used' ? 'Utilizzato' :
                     status === 'rejected' ? 'Rifiutato' : status}
                  </span>
                </div>
                <span className="text-sm font-semibold text-gray-900">{count}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Popular Rewards */}
        <div className="bg-white rounded-lg p-6 shadow-sm border">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Premi Più Popolari</h3>
          <div className="space-y-3">
            {popular_rewards?.slice(0, 5).map((item, index) => (
              <div key={item.reward.id} className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className="text-lg font-bold text-imagross-orange">#{index + 1}</div>
                  <div>
                    <div className="text-sm font-medium text-gray-900">{item.reward.title}</div>
                    <div className="text-xs text-gray-600">{item.reward.category}</div>
                  </div>
                </div>
                <div className="text-sm font-semibold text-purple-600">{item.redemption_count} riscatti</div>
              </div>
            ))}
            {(!popular_rewards || popular_rewards.length === 0) && (
              <p className="text-gray-500 text-sm">Nessun premio riscattato ancora</p>
            )}
          </div>
        </div>
      </div>

      {/* Time Series Chart - Simplified */}
      <div className="bg-white rounded-lg p-6 shadow-sm border">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Riscatti Ultimi 30 Giorni</h3>
        <div className="h-64 flex items-end space-x-1">
          {time_series?.daily_redemptions?.map((day, index) => (
            <div key={day.date} className="flex-1 bg-imagrost-orange opacity-75 hover:opacity-100 transition-opacity" 
                 style={{ height: `${Math.max(4, (day.redemptions / Math.max(...time_series.daily_redemptions.map(d => d.redemptions), 1)) * 100)}%` }}
                 title={`${day.date}: ${day.redemptions} riscatti`}>
            </div>
          ))}
        </div>
        <div className="mt-2 text-xs text-gray-500 text-center">
          Ultimi 30 giorni - Hover per dettagli
        </div>
      </div>

      {/* Category Performance */}
      <div className="bg-white rounded-lg p-6 shadow-sm border">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Performance per Categoria</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Categoria</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Premi Totali</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Premi Attivi</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Riscatti</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Tasso Successo</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {Object.entries(category_stats || {}).map(([category, stats]) => (
                <tr key={category}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{category}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{stats.total}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{stats.active}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{stats.redemptions}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {stats.active > 0 ? Math.round((stats.redemptions / stats.active) * 100) : 0}%
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};