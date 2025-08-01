import React, { useState, useEffect } from 'react';

export const CreateRewardModal = ({ onClose, onCreate, categories }) => {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    type: 'discount_percentage',
    category: 'Sconti',
    discount_percentage: '',
    discount_amount: '',
    product_sku: '',
    custom_instructions: '',
    bollini_required: '',
    min_purchase_amount: '',
    max_discount_amount: '',
    loyalty_level_required: '',
    total_stock: '',
    max_redemptions_per_user: '',
    max_uses_per_redemption: 1,
    expiry_type: 'fixed_date',
    expiry_date: '',
    expiry_days_from_creation: '',
    expiry_days_from_redemption: '',
    icon: '🎁',
    color: '#FF6B35',
    featured: false,
    sort_order: 0,
    terms_and_conditions: '',
    usage_instructions: ''
  });

  const [errors, setErrors] = useState({});

  const rewardTypes = [
    { value: 'discount_percentage', label: 'Sconto Percentuale' },
    { value: 'discount_fixed', label: 'Sconto Fisso' },
    { value: 'free_product', label: 'Prodotto Gratuito' },
    { value: 'voucher', label: 'Buono Spesa' },
    { value: 'free_shipping', label: 'Spedizione Gratuita' },
    { value: 'vip_access', label: 'Accesso VIP' },
    { value: 'custom', label: 'Personalizzato' }
  ];

  const expiryTypes = [
    { value: 'fixed_date', label: 'Data Fissa' },
    { value: 'days_from_creation', label: 'Giorni dalla Creazione' },
    { value: 'days_from_redemption', label: 'Giorni dal Riscatto' }
  ];

  const loyaltyLevels = ['Bronze', 'Silver', 'Gold', 'Platinum'];

  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: null }));
    }
  };

  const validateForm = () => {
    const newErrors = {};

    if (!formData.title.trim()) newErrors.title = 'Titolo richiesto';
    if (!formData.description.trim()) newErrors.description = 'Descrizione richiesta';
    if (!formData.bollini_required || formData.bollini_required < 0) newErrors.bollini_required = 'Bollini richiesti';

    // Type-specific validation
    if (formData.type === 'discount_percentage' && (!formData.discount_percentage || formData.discount_percentage < 1 || formData.discount_percentage > 100)) {
      newErrors.discount_percentage = 'Percentuale tra 1 e 100';
    }
    if ((formData.type === 'discount_fixed' || formData.type === 'voucher') && (!formData.discount_amount || formData.discount_amount <= 0)) {
      newErrors.discount_amount = 'Importo richiesto';
    }
    if (formData.type === 'free_product' && !formData.product_sku.trim()) {
      newErrors.product_sku = 'SKU prodotto richiesto';
    }
    if (formData.type === 'custom' && !formData.custom_instructions.trim()) {
      newErrors.custom_instructions = 'Istruzioni richieste';
    }

    // Expiry validation
    if (formData.expiry_type === 'fixed_date' && !formData.expiry_date) {
      newErrors.expiry_date = 'Data scadenza richiesta';
    }
    if (formData.expiry_type === 'days_from_creation' && (!formData.expiry_days_from_creation || formData.expiry_days_from_creation < 1)) {
      newErrors.expiry_days_from_creation = 'Giorni richiesti';
    }
    if (formData.expiry_type === 'days_from_redemption' && (!formData.expiry_days_from_redemption || formData.expiry_days_from_redemption < 1)) {
      newErrors.expiry_days_from_redemption = 'Giorni richiesti';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (validateForm()) {
      // Convert string numbers to numbers
      const submitData = {
        ...formData,
        bollini_required: parseInt(formData.bollini_required),
        discount_percentage: formData.discount_percentage ? parseInt(formData.discount_percentage) : null,
        discount_amount: formData.discount_amount ? parseFloat(formData.discount_amount) : null,
        min_purchase_amount: formData.min_purchase_amount ? parseFloat(formData.min_purchase_amount) : null,
        max_discount_amount: formData.max_discount_amount ? parseFloat(formData.max_discount_amount) : null,
        total_stock: formData.total_stock ? parseInt(formData.total_stock) : null,
        max_redemptions_per_user: formData.max_redemptions_per_user ? parseInt(formData.max_redemptions_per_user) : null,
        max_uses_per_redemption: parseInt(formData.max_uses_per_redemption),
        expiry_days_from_creation: formData.expiry_days_from_creation ? parseInt(formData.expiry_days_from_creation) : null,
        expiry_days_from_redemption: formData.expiry_days_from_redemption ? parseInt(formData.expiry_days_from_redemption) : null,
        sort_order: parseInt(formData.sort_order),
        expiry_date: formData.expiry_date ? new Date(formData.expiry_date).toISOString() : null
      };

      onCreate(submitData);
    }
  };

  const renderValueFields = () => {
    switch (formData.type) {
      case 'discount_percentage':
        return (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Percentuale Sconto (%)</label>
            <input
              type="number"
              min="1"
              max="100"
              value={formData.discount_percentage}
              onChange={(e) => handleInputChange('discount_percentage', e.target.value)}
              className={`w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-imagross-orange focus:border-transparent ${errors.discount_percentage ? 'border-red-300' : 'border-gray-300'}`}
            />
            {errors.discount_percentage && <p className="text-red-500 text-xs mt-1">{errors.discount_percentage}</p>}
          </div>
        );
      case 'discount_fixed':
      case 'voucher':
        return (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Importo (€)</label>
            <input
              type="number"
              min="0"
              step="0.01"
              value={formData.discount_amount}
              onChange={(e) => handleInputChange('discount_amount', e.target.value)}
              className={`w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-imagross-orange focus:border-transparent ${errors.discount_amount ? 'border-red-300' : 'border-gray-300'}`}
            />
            {errors.discount_amount && <p className="text-red-500 text-xs mt-1">{errors.discount_amount}</p>}
          </div>
        );
      case 'free_product':
        return (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">SKU Prodotto</label>
            <input
              type="text"
              value={formData.product_sku}
              onChange={(e) => handleInputChange('product_sku', e.target.value)}
              className={`w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-imagross-orange focus:border-transparent ${errors.product_sku ? 'border-red-300' : 'border-gray-300'}`}
            />
            {errors.product_sku && <p className="text-red-500 text-xs mt-1">{errors.product_sku}</p>}
          </div>
        );
      case 'custom':
        return (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Istruzioni Personalizzate</label>
            <textarea
              value={formData.custom_instructions}
              onChange={(e) => handleInputChange('custom_instructions', e.target.value)}
              rows="3"
              className={`w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-imagross-orange focus:border-transparent ${errors.custom_instructions ? 'border-red-300' : 'border-gray-300'}`}
            />
            {errors.custom_instructions && <p className="text-red-500 text-xs mt-1">{errors.custom_instructions}</p>}
          </div>
        );
      default:
        return null;
    }
  };

  const renderExpiryFields = () => {
    switch (formData.expiry_type) {
      case 'fixed_date':
        return (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Data Scadenza</label>
            <input
              type="date"
              value={formData.expiry_date}
              onChange={(e) => handleInputChange('expiry_date', e.target.value)}
              className={`w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-imagross-orange focus:border-transparent ${errors.expiry_date ? 'border-red-300' : 'border-gray-300'}`}
            />
            {errors.expiry_date && <p className="text-red-500 text-xs mt-1">{errors.expiry_date}</p>}
          </div>
        );
      case 'days_from_creation':
        return (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Giorni dalla Creazione</label>
            <input
              type="number"
              min="1"
              value={formData.expiry_days_from_creation}
              onChange={(e) => handleInputChange('expiry_days_from_creation', e.target.value)}
              className={`w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-imagross-orange focus:border-transparent ${errors.expiry_days_from_creation ? 'border-red-300' : 'border-gray-300'}`}
            />
            {errors.expiry_days_from_creation && <p className="text-red-500 text-xs mt-1">{errors.expiry_days_from_creation}</p>}
          </div>
        );
      case 'days_from_redemption':
        return (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Giorni dal Riscatto</label>
            <input
              type="number"
              min="1"
              value={formData.expiry_days_from_redemption}
              onChange={(e) => handleInputChange('expiry_days_from_redemption', e.target.value)}
              className={`w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-imagross-orange focus:border-transparent ${errors.expiry_days_from_redemption ? 'border-red-300' : 'border-gray-300'}`}
            />
            {errors.expiry_days_from_redemption && <p className="text-red-500 text-xs mt-1">{errors.expiry_days_from_redemption}</p>}
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-10 mx-auto p-5 border w-11/12 max-w-4xl shadow-lg rounded-md bg-white">
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-2xl font-bold text-gray-900">Crea Nuovo Premio</h3>
            <button
              type="button"
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Left Column */}
            <div className="space-y-4">
              <h4 className="text-lg font-semibold text-gray-900 border-b pb-2">Informazioni Base</h4>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Titolo *</label>
                <input
                  type="text"
                  value={formData.title}
                  onChange={(e) => handleInputChange('title', e.target.value)}
                  className={`w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-imagross-orange focus:border-transparent ${errors.title ? 'border-red-300' : 'border-gray-300'}`}
                />
                {errors.title && <p className="text-red-500 text-xs mt-1">{errors.title}</p>}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Descrizione *</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => handleInputChange('description', e.target.value)}
                  rows="3"
                  className={`w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-imagross-orange focus:border-transparent ${errors.description ? 'border-red-300' : 'border-gray-300'}`}
                />
                {errors.description && <p className="text-red-500 text-xs mt-1">{errors.description}</p>}
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Tipo Premio</label>
                  <select
                    value={formData.type}
                    onChange={(e) => handleInputChange('type', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-imagross-orange focus:border-transparent"
                  >
                    {rewardTypes.map(type => (
                      <option key={type.value} value={type.value}>{type.label}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Categoria</label>
                  <select
                    value={formData.category}
                    onChange={(e) => handleInputChange('category', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-imagross-orange focus:border-transparent"
                  >
                    {categories.map(cat => (
                      <option key={cat} value={cat}>{cat}</option>
                    ))}
                  </select>
                </div>
              </div>

              {renderValueFields()}

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Bollini Richiesti *</label>
                <input
                  type="number"
                  min="0"
                  value={formData.bollini_required}
                  onChange={(e) => handleInputChange('bollini_required', e.target.value)}
                  className={`w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-imagross-orange focus:border-transparent ${errors.bollini_required ? 'border-red-300' : 'border-gray-300'}`}
                />
                {errors.bollini_required && <p className="text-red-500 text-xs mt-1">{errors.bollini_required}</p>}
              </div>
            </div>

            {/* Right Column */}
            <div className="space-y-4">
              <h4 className="text-lg font-semibold text-gray-900 border-b pb-2">Configurazione Avanzata</h4>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Acquisto Minimo (€)</label>
                  <input
                    type="number"
                    min="0"
                    step="0.01"
                    value={formData.min_purchase_amount}
                    onChange={(e) => handleInputChange('min_purchase_amount', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-imagross-orange focus:border-transparent"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Sconto Max (€)</label>
                  <input
                    type="number"
                    min="0"
                    step="0.01"
                    value={formData.max_discount_amount}
                    onChange={(e) => handleInputChange('max_discount_amount', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-imagross-orange focus:border-transparent"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Livello Fidelity Richiesto</label>
                <select
                  value={formData.loyalty_level_required}
                  onChange={(e) => handleInputChange('loyalty_level_required', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-imagross-orange focus:border-transparent"
                >
                  <option value="">Nessun requisito</option>
                  {loyaltyLevels.map(level => (
                    <option key={level} value={level}>{level}</option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Stock Totale</label>
                  <input
                    type="number"
                    min="0"
                    value={formData.total_stock}
                    onChange={(e) => handleInputChange('total_stock', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-imagross-orange focus:border-transparent"
                    placeholder="Lascia vuoto per illimitato"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Max per Utente</label>
                  <input
                    type="number"
                    min="1"
                    value={formData.max_redemptions_per_user}
                    onChange={(e) => handleInputChange('max_redemptions_per_user', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-imagross-orange focus:border-transparent"
                    placeholder="Lascia vuoto per illimitato"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Tipo Scadenza</label>
                <select
                  value={formData.expiry_type}
                  onChange={(e) => handleInputChange('expiry_type', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-imagross-orange focus:border-transparent"
                >
                  {expiryTypes.map(type => (
                    <option key={type.value} value={type.value}>{type.label}</option>
                  ))}
                </select>
              </div>

              {renderExpiryFields()}

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Icona</label>
                  <input
                    type="text"
                    value={formData.icon}
                    onChange={(e) => handleInputChange('icon', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-imagross-orange focus:border-transparent"
                    placeholder="🎁"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Colore</label>
                  <input
                    type="color"
                    value={formData.color}
                    onChange={(e) => handleInputChange('color', e.target.value)}
                    className="w-full h-10 border border-gray-300 rounded-md focus:ring-2 focus:ring-imagross-orange focus:border-transparent"
                  />
                </div>
              </div>

              <div className="flex items-center space-x-4">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={formData.featured}
                    onChange={(e) => handleInputChange('featured', e.target.checked)}
                    className="h-4 w-4 text-imagross-orange focus:ring-imagross-orange border-gray-300 rounded"
                  />
                  <span className="ml-2 text-sm text-gray-700">In evidenza</span>
                </label>
              </div>
            </div>
          </div>

          {/* Terms */}
          <div className="space-y-4">
            <h4 className="text-lg font-semibold text-gray-900 border-b pb-2">Termini e Condizioni</h4>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Istruzioni d'Uso</label>
              <textarea
                value={formData.usage_instructions}
                onChange={(e) => handleInputChange('usage_instructions', e.target.value)}
                rows="2"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-imagross-orange focus:border-transparent"
                placeholder="Come utilizzare questo premio..."
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Termini e Condizioni</label>
              <textarea
                value={formData.terms_and_conditions}
                onChange={(e) => handleInputChange('terms_and_conditions', e.target.value)}
                rows="3"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-imagross-orange focus:border-transparent"
                placeholder="Termini e condizioni del premio..."
              />
            </div>
          </div>

          {/* Actions */}
          <div className="flex justify-end space-x-3 pt-6 border-t border-gray-200">
            <button
              type="button"
              onClick={onClose}
              className="px-6 py-2 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400 transition-colors"
            >
              Annulla
            </button>
            <button
              type="submit"
              className="px-6 py-2 bg-imagross-orange text-white rounded-lg hover:bg-imagross-red transition-colors"
            >
              Crea Premio
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export const EditRewardModal = ({ reward, onClose, onUpdate, categories }) => {
  const [formData, setFormData] = useState({});

  useEffect(() => {
    if (reward) {
      setFormData({
        title: reward.title || '',
        description: reward.description || '',
        status: reward.status || 'active',
        discount_percentage: reward.discount_percentage || '',
        discount_amount: reward.discount_amount || '',
        product_sku: reward.product_sku || '',
        custom_instructions: reward.custom_instructions || '',
        bollini_required: reward.bollini_required || '',
        min_purchase_amount: reward.min_purchase_amount || '',
        max_discount_amount: reward.max_discount_amount || '',
        loyalty_level_required: reward.loyalty_level_required || '',
        total_stock: reward.total_stock || '',
        max_redemptions_per_user: reward.max_redemptions_per_user || '',
        max_uses_per_redemption: reward.max_uses_per_redemption || 1,
        expiry_type: reward.expiry_type || 'fixed_date',
        expiry_date: reward.expiry_date ? new Date(reward.expiry_date).toISOString().split('T')[0] : '',
        expiry_days_from_creation: reward.expiry_days_from_creation || '',
        expiry_days_from_redemption: reward.expiry_days_from_redemption || '',
        icon: reward.icon || '🎁',
        color: reward.color || '#FF6B35',
        featured: reward.featured || false,
        sort_order: reward.sort_order || 0,
        terms_and_conditions: reward.terms_and_conditions || '',
        usage_instructions: reward.usage_instructions || ''
      });
    }
  }, [reward]);

  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    
    // Convert string numbers to numbers
    const submitData = {
      ...formData,
      bollini_required: formData.bollini_required ? parseInt(formData.bollini_required) : null,
      discount_percentage: formData.discount_percentage ? parseInt(formData.discount_percentage) : null,
      discount_amount: formData.discount_amount ? parseFloat(formData.discount_amount) : null,
      min_purchase_amount: formData.min_purchase_amount ? parseFloat(formData.min_purchase_amount) : null,
      max_discount_amount: formData.max_discount_amount ? parseFloat(formData.max_discount_amount) : null,
      total_stock: formData.total_stock ? parseInt(formData.total_stock) : null,
      max_redemptions_per_user: formData.max_redemptions_per_user ? parseInt(formData.max_redemptions_per_user) : null,
      max_uses_per_redemption: parseInt(formData.max_uses_per_redemption),
      expiry_days_from_creation: formData.expiry_days_from_creation ? parseInt(formData.expiry_days_from_creation) : null,
      expiry_days_from_redemption: formData.expiry_days_from_redemption ? parseInt(formData.expiry_days_from_redemption) : null,
      sort_order: parseInt(formData.sort_order),
      expiry_date: formData.expiry_date ? new Date(formData.expiry_date).toISOString() : null
    };

    // Remove null values
    const cleanedData = Object.fromEntries(
      Object.entries(submitData).filter(([_, value]) => value !== null && value !== '')
    );

    onUpdate(reward.id, cleanedData);
  };

  if (!reward) return null;

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-10 mx-auto p-5 border w-11/12 max-w-3xl shadow-lg rounded-md bg-white">
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-2xl font-bold text-gray-900">Modifica Premio</h3>
            <button
              type="button"
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Titolo</label>
                <input
                  type="text"
                  value={formData.title}
                  onChange={(e) => handleInputChange('title', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-imagross-orange focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Descrizione</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => handleInputChange('description', e.target.value)}
                  rows="3"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-imagross-orange focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Stato</label>
                <select
                  value={formData.status}
                  onChange={(e) => handleInputChange('status', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-imagross-orange focus:border-transparent"
                >
                  <option value="active">Attivo</option>
                  <option value="inactive">Inattivo</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Bollini Richiesti</label>
                <input
                  type="number"
                  min="0"
                  value={formData.bollini_required}
                  onChange={(e) => handleInputChange('bollini_required', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-imagross-orange focus:border-transparent"
                />
              </div>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Stock Totale</label>
                <input
                  type="number"
                  min="0"
                  value={formData.total_stock}
                  onChange={(e) => handleInputChange('total_stock', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-imagross-orange focus:border-transparent"
                  placeholder="Lascia vuoto per illimitato"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Max Riscatti per Utente</label>
                <input
                  type="number"
                  min="1"
                  value={formData.max_redemptions_per_user}
                  onChange={(e) => handleInputChange('max_redemptions_per_user', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-imagross-orange focus:border-transparent"
                  placeholder="Lascia vuoto per illimitato"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Icona</label>
                  <input
                    type="text"
                    value={formData.icon}
                    onChange={(e) => handleInputChange('icon', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-imagross-orange focus:border-transparent"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Colore</label>
                  <input
                    type="color"
                    value={formData.color}
                    onChange={(e) => handleInputChange('color', e.target.value)}
                    className="w-full h-10 border border-gray-300 rounded-md focus:ring-2 focus:ring-imagross-orange focus:border-transparent"
                  />
                </div>
              </div>

              <div className="flex items-center space-x-4">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={formData.featured}
                    onChange={(e) => handleInputChange('featured', e.target.checked)}
                    className="h-4 w-4 text-imagross-orange focus:ring-imagross-orange border-gray-300 rounded"
                  />
                  <span className="ml-2 text-sm text-gray-700">In evidenza</span>
                </label>
              </div>
            </div>
          </div>

          <div className="flex justify-end space-x-3 pt-6 border-t border-gray-200">
            <button
              type="button"
              onClick={onClose}
              className="px-6 py-2 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400 transition-colors"
            >
              Annulla
            </button>
            <button
              type="submit"
              className="px-6 py-2 bg-imagross-orange text-white rounded-lg hover:bg-imagross-red transition-colors"
            >
              Salva Modifiche
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export const ProcessRedemptionModal = ({ redemption, onClose, onProcess }) => {
  const [action, setAction] = useState('approve');
  const [adminNotes, setAdminNotes] = useState('');
  const [rejectionReason, setRejectionReason] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    onProcess(redemption.id, action, adminNotes, rejectionReason);
  };

  if (!redemption) return null;

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-10 mx-auto p-5 border w-11/12 max-w-2xl shadow-lg rounded-md bg-white">
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-2xl font-bold text-gray-900">Gestisci Riscatto</h3>
            <button
              type="button"
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Redemption Info */}
          <div className="bg-gray-50 rounded-lg p-4">
            <h4 className="font-semibold text-gray-900 mb-2">Dettagli Riscatto</h4>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="font-medium text-gray-600">Codice:</span>
                <span className="ml-2 font-mono text-imagross-orange">{redemption.redemption_code}</span>
              </div>
              <div>
                <span className="font-medium text-gray-600">Premio:</span>
                <span className="ml-2">{redemption.reward_info?.title}</span>
              </div>
              <div>
                <span className="font-medium text-gray-600">Utente:</span>
                <span className="ml-2">{redemption.user_info?.nome} {redemption.user_info?.cognome}</span>
              </div>
              <div>
                <span className="font-medium text-gray-600">Data Riscatto:</span>
                <span className="ml-2">{new Date(redemption.redeemed_at).toLocaleDateString('it-IT')}</span>
              </div>
            </div>
          </div>

          {/* Action Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Azione</label>
            <div className="flex space-x-4">
              <label className="flex items-center">
                <input
                  type="radio"
                  value="approve"
                  checked={action === 'approve'}
                  onChange={(e) => setAction(e.target.value)}
                  className="h-4 w-4 text-green-600 focus:ring-green-500 border-gray-300"
                />
                <span className="ml-2 text-sm text-gray-700">Approva</span>
              </label>
              <label className="flex items-center">
                <input
                  type="radio"
                  value="reject"
                  checked={action === 'reject'}
                  onChange={(e) => setAction(e.target.value)}
                  className="h-4 w-4 text-red-600 focus:ring-red-500 border-gray-300"
                />
                <span className="ml-2 text-sm text-gray-700">Rifiuta</span>
              </label>
            </div>
          </div>

          {/* Rejection Reason */}
          {action === 'reject' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Motivo Rifiuto</label>
              <select
                value={rejectionReason}
                onChange={(e) => setRejectionReason(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-imagross-orange focus:border-transparent"
                required
              >
                <option value="">Seleziona motivo</option>
                <option value="insufficient_requirements">Requisiti insufficienti</option>
                <option value="suspicious_activity">Attività sospetta</option>
                <option value="technical_issue">Problema tecnico</option>
                <option value="policy_violation">Violazione policy</option>
                <option value="other">Altro</option>
              </select>
            </div>
          )}

          {/* Admin Notes */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Note Admin</label>
            <textarea
              value={adminNotes}
              onChange={(e) => setAdminNotes(e.target.value)}
              rows="3"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-imagross-orange focus:border-transparent"
              placeholder="Note interne per questo riscatto..."
            />
          </div>

          {/* Actions */}
          <div className="flex justify-end space-x-3 pt-6 border-t border-gray-200">
            <button
              type="button"
              onClick={onClose}
              className="px-6 py-2 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400 transition-colors"
            >
              Annulla
            </button>
            <button
              type="submit"
              className={`px-6 py-2 text-white rounded-lg transition-colors ${
                action === 'approve' 
                  ? 'bg-green-600 hover:bg-green-700' 
                  : 'bg-red-600 hover:bg-red-700'
              }`}
            >
              {action === 'approve' ? 'Approva Riscatto' : 'Rifiuta Riscatto'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};