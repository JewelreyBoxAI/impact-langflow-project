/**
 * Zoho CRM Data Table Component
 * Displays and manages Zoho CRM records (Leads, Contacts, Accounts)
 */

'use client'

import * as React from 'react'
import { Badge } from '@/components/shared/Badge'
import { Button } from '@/components/shared/Button'
import { Avatar } from '@/components/shared/Avatar'
import { cn } from '@/lib/utils'
import {
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Mail,
  MoreHorizontal,
  Phone,
  RefreshCw,
  Search,
  Star,
  User,
  Users,
  Building,
  Calendar,
  Eye,
  Edit,
  Trash2
} from 'lucide-react'
import type {
  ZohoCRMDataTableProps,
  ZohoMCPLead,
  ZohoMCPContact,
  ZohoMCPAccount
} from '@/lib/types/mcp'

interface TableColumn {
  key: string
  label: string
  sortable?: boolean
  width?: string
  render?: (value: any, record: any) => React.ReactNode
}

interface SortConfig {
  key: string
  direction: 'asc' | 'desc'
}

export const ZohoCRMDataTable: React.FC<ZohoCRMDataTableProps> = ({
  module,
  data,
  isLoading = false,
  onRefresh,
  onRowSelect,
  className
}) => {
  const [sortConfig, setSortConfig] = React.useState<SortConfig | null>(null)
  const [searchQuery, setSearchQuery] = React.useState('')
  const [selectedRows, setSelectedRows] = React.useState<Set<string>>(new Set())

  // Define columns based on module type
  const getColumns = (): TableColumn[] => {
    const baseColumns: TableColumn[] = [
      {
        key: 'select',
        label: '',
        width: 'w-12',
        render: (_, record) => (
          <input
            type="checkbox"
            checked={selectedRows.has(record.id)}
            onChange={(e) => {
              const newSelected = new Set(selectedRows)
              if (e.target.checked) {
                newSelected.add(record.id)
              } else {
                newSelected.delete(record.id)
              }
              setSelectedRows(newSelected)
            }}
            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
          />
        )
      }
    ]

    switch (module) {
      case 'Leads':
        return [
          ...baseColumns,
          {
            key: 'name',
            label: 'Name',
            sortable: true,
            render: (_, record: ZohoMCPLead) => (
              <div className="flex items-center gap-3">
                <Avatar
                  name={`${record.firstName} ${record.lastName}`}
                  size="sm"
                />
                <div>
                  <div className="font-medium">
                    {record.firstName} {record.lastName}
                  </div>
                  <div className="text-sm text-muted-foreground">
                    {record.designation} {record.company && `at ${record.company}`}
                  </div>
                </div>
              </div>
            )
          },
          {
            key: 'contact',
            label: 'Contact',
            render: (_, record: ZohoMCPLead) => (
              <div className="space-y-1">
                {record.email && (
                  <div className="flex items-center gap-2 text-sm">
                    <Mail className="h-3 w-3 text-muted-foreground" />
                    <span>{record.email}</span>
                  </div>
                )}
                {(record.phone || record.mobile) && (
                  <div className="flex items-center gap-2 text-sm">
                    <Phone className="h-3 w-3 text-muted-foreground" />
                    <span>{record.phone || record.mobile}</span>
                  </div>
                )}
              </div>
            )
          },
          {
            key: 'status',
            label: 'Status',
            sortable: true,
            render: (_, record: ZohoMCPLead) => (
              <div className="space-y-2">
                <Badge variant="outline">{record.leadStatus}</Badge>
                {record.rating && (
                  <Badge
                    variant={
                      record.rating === 'Hot' ? 'destructive' :
                      record.rating === 'Warm' ? 'warning' : 'secondary'
                    }
                  >
                    {record.rating}
                  </Badge>
                )}
              </div>
            )
          },
          {
            key: 'source',
            label: 'Source',
            sortable: true,
            render: (_, record: ZohoMCPLead) => (
              <Badge variant="secondary">{record.leadSource}</Badge>
            )
          },
          {
            key: 'score',
            label: 'Score',
            sortable: true,
            render: (_, record: ZohoMCPLead) => (
              record.leadScore ? (
                <div className="flex items-center gap-1">
                  <Star className="h-3 w-3 text-yellow-500" />
                  <span className="text-sm font-medium">{record.leadScore}</span>
                </div>
              ) : (
                <span className="text-muted-foreground text-sm">N/A</span>
              )
            )
          }
        ]

      case 'Contacts':
        return [
          ...baseColumns,
          {
            key: 'name',
            label: 'Name',
            sortable: true,
            render: (_, record: ZohoMCPContact) => (
              <div className="flex items-center gap-3">
                <Avatar
                  name={`${record.firstName} ${record.lastName}`}
                  size="sm"
                />
                <div>
                  <div className="font-medium">
                    {record.firstName} {record.lastName}
                  </div>
                  <div className="text-sm text-muted-foreground">
                    {record.title} {record.department && `• ${record.department}`}
                  </div>
                </div>
              </div>
            )
          },
          {
            key: 'contact',
            label: 'Contact',
            render: (_, record: ZohoMCPContact) => (
              <div className="space-y-1">
                {record.email && (
                  <div className="flex items-center gap-2 text-sm">
                    <Mail className="h-3 w-3 text-muted-foreground" />
                    <span>{record.email}</span>
                  </div>
                )}
                {(record.phone || record.mobile) && (
                  <div className="flex items-center gap-2 text-sm">
                    <Phone className="h-3 w-3 text-muted-foreground" />
                    <span>{record.phone || record.mobile}</span>
                  </div>
                )}
              </div>
            )
          },
          {
            key: 'account',
            label: 'Account',
            sortable: true,
            render: (_, record: ZohoMCPContact) => (
              record.accountName ? (
                <div className="flex items-center gap-2">
                  <Building className="h-3 w-3 text-muted-foreground" />
                  <span className="text-sm">{record.accountName}</span>
                </div>
              ) : (
                <span className="text-muted-foreground text-sm">N/A</span>
              )
            )
          },
          {
            key: 'owner',
            label: 'Owner',
            render: (_, record: ZohoMCPContact) => (
              <div className="flex items-center gap-2">
                <User className="h-3 w-3 text-muted-foreground" />
                <span className="text-sm">{record.contactOwner.name}</span>
              </div>
            )
          }
        ]

      case 'Accounts':
        return [
          ...baseColumns,
          {
            key: 'name',
            label: 'Account Name',
            sortable: true,
            render: (_, record: ZohoMCPAccount) => (
              <div className="flex items-center gap-3">
                <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white text-sm font-semibold">
                  {record.accountName.charAt(0).toUpperCase()}
                </div>
                <div>
                  <div className="font-medium">{record.accountName}</div>
                  {record.industry && (
                    <div className="text-sm text-muted-foreground">{record.industry}</div>
                  )}
                </div>
              </div>
            )
          },
          {
            key: 'contact',
            label: 'Contact',
            render: (_, record: ZohoMCPAccount) => (
              <div className="space-y-1">
                {record.website && (
                  <div className="flex items-center gap-2 text-sm">
                    <ExternalLink className="h-3 w-3 text-muted-foreground" />
                    <a
                      href={record.website}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:underline"
                    >
                      {record.website}
                    </a>
                  </div>
                )}
                {record.phone && (
                  <div className="flex items-center gap-2 text-sm">
                    <Phone className="h-3 w-3 text-muted-foreground" />
                    <span>{record.phone}</span>
                  </div>
                )}
              </div>
            )
          },
          {
            key: 'details',
            label: 'Details',
            render: (_, record: ZohoMCPAccount) => (
              <div className="space-y-1 text-sm text-muted-foreground">
                {record.employees && (
                  <div className="flex items-center gap-2">
                    <Users className="h-3 w-3" />
                    <span>{record.employees.toLocaleString()} employees</span>
                  </div>
                )}
                {record.annualRevenue && (
                  <div>
                    Revenue: ${record.annualRevenue.toLocaleString()}
                  </div>
                )}
                {record.type && (
                  <Badge variant="outline" className="text-xs">{record.type}</Badge>
                )}
              </div>
            )
          },
          {
            key: 'owner',
            label: 'Owner',
            render: (_, record: ZohoMCPAccount) => (
              <div className="flex items-center gap-2">
                <User className="h-3 w-3 text-muted-foreground" />
                <span className="text-sm">{record.accountOwner.name}</span>
              </div>
            )
          }
        ]

      default:
        return baseColumns
    }
  }

  // Add common columns
  const columns = [
    ...getColumns(),
    {
      key: 'created',
      label: 'Created',
      sortable: true,
      render: (_, record: any) => (
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Calendar className="h-3 w-3" />
          <span>{new Date(record.createdTime).toLocaleDateString()}</span>
        </div>
      )
    },
    {
      key: 'actions',
      label: '',
      width: 'w-16',
      render: (_, record: any) => (
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="icon"
            className="h-6 w-6"
            onClick={() => onRowSelect?.(record)}
            title="View details"
          >
            <Eye className="h-3 w-3" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="h-6 w-6"
            title="More actions"
          >
            <MoreHorizontal className="h-3 w-3" />
          </Button>
        </div>
      )
    }
  ]

  // Filter data based on search query
  const filteredData = React.useMemo(() => {
    if (!searchQuery.trim()) return data

    return data.filter((record: any) => {
      const searchableFields = [
        record.firstName,
        record.lastName,
        record.accountName,
        record.email,
        record.company,
        record.phone,
        record.mobile
      ].filter(Boolean)

      return searchableFields.some(field =>
        field.toLowerCase().includes(searchQuery.toLowerCase())
      )
    })
  }, [data, searchQuery])

  // Sort data
  const sortedData = React.useMemo(() => {
    if (!sortConfig) return filteredData

    return [...filteredData].sort((a: any, b: any) => {
      let aValue = a[sortConfig.key]
      let bValue = b[sortConfig.key]

      // Special handling for name field
      if (sortConfig.key === 'name') {
        aValue = `${a.firstName || ''} ${a.lastName || ''} ${a.accountName || ''}`.trim()
        bValue = `${b.firstName || ''} ${b.lastName || ''} ${b.accountName || ''}`.trim()
      }

      if (aValue < bValue) return sortConfig.direction === 'asc' ? -1 : 1
      if (aValue > bValue) return sortConfig.direction === 'asc' ? 1 : -1
      return 0
    })
  }, [filteredData, sortConfig])

  const handleSort = (key: string) => {
    setSortConfig(current => {
      if (current?.key === key) {
        return {
          key,
          direction: current.direction === 'asc' ? 'desc' : 'asc'
        }
      }
      return { key, direction: 'asc' }
    })
  }

  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      setSelectedRows(new Set(sortedData.map((record: any) => record.id)))
    } else {
      setSelectedRows(new Set())
    }
  }

  const getSortIcon = (key: string) => {
    if (!sortConfig || sortConfig.key !== key) {
      return <ChevronDown className="h-3 w-3 text-muted-foreground opacity-0 group-hover:opacity-100" />
    }
    return sortConfig.direction === 'asc' ?
      <ChevronUp className="h-3 w-3 text-foreground" /> :
      <ChevronDown className="h-3 w-3 text-foreground" />
  }

  return (
    <div className={cn('space-y-4', className)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="font-semibold text-lg">
            {module} ({sortedData.length})
          </h3>
          <p className="text-sm text-muted-foreground">
            Manage your Zoho CRM {module.toLowerCase()}
          </p>
        </div>

        <div className="flex items-center gap-2">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <input
              type="text"
              placeholder={`Search ${module.toLowerCase()}...`}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 pr-4 py-2 border border-input bg-background rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent"
            />
          </div>

          {/* Refresh */}
          {onRefresh && (
            <Button
              variant="outline"
              size="icon"
              onClick={onRefresh}
              disabled={isLoading}
              title="Refresh data"
            >
              <RefreshCw className={cn('h-4 w-4', isLoading && 'animate-spin')} />
            </Button>
          )}
        </div>
      </div>

      {/* Table */}
      <div className="rounded-lg border bg-card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-muted/50">
              <tr>
                <th className="w-12 p-3 text-left">
                  <input
                    type="checkbox"
                    checked={selectedRows.size === sortedData.length && sortedData.length > 0}
                    onChange={(e) => handleSelectAll(e.target.checked)}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                </th>
                {columns.slice(1).map((column) => (
                  <th
                    key={column.key}
                    className={cn(
                      'p-3 text-left text-sm font-medium text-muted-foreground',
                      column.width,
                      column.sortable && 'cursor-pointer hover:text-foreground group'
                    )}
                    onClick={() => column.sortable && handleSort(column.key)}
                  >
                    <div className="flex items-center gap-2">
                      {column.label}
                      {column.sortable && getSortIcon(column.key)}
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {sortedData.map((record: any, index: number) => (
                <tr
                  key={record.id}
                  className={cn(
                    'border-t hover:bg-muted/25 transition-colors',
                    selectedRows.has(record.id) && 'bg-muted/50'
                  )}
                >
                  {columns.map((column) => (
                    <td key={column.key} className={cn('p-3', column.width)}>
                      {column.render ? column.render(record[column.key], record) : record[column.key]}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Empty State */}
        {sortedData.length === 0 && !isLoading && (
          <div className="p-8 text-center">
            <div className="mx-auto h-12 w-12 text-muted-foreground mb-4">
              {module === 'Leads' && <User className="h-full w-full" />}
              {module === 'Contacts' && <Users className="h-full w-full" />}
              {module === 'Accounts' && <Building className="h-full w-full" />}
            </div>
            <h4 className="font-medium text-lg mb-2">No {module} Found</h4>
            <p className="text-sm text-muted-foreground">
              {searchQuery
                ? `No ${module.toLowerCase()} match your search criteria.`
                : `No ${module.toLowerCase()} available. Connect to Zoho CRM to sync data.`
              }
            </p>
          </div>
        )}

        {/* Loading State */}
        {isLoading && (
          <div className="p-8 text-center">
            <RefreshCw className="h-8 w-8 text-muted-foreground mx-auto mb-4 animate-spin" />
            <h4 className="font-medium text-lg mb-2">Loading {module}</h4>
            <p className="text-sm text-muted-foreground">
              Fetching data from Zoho CRM...
            </p>
          </div>
        )}
      </div>

      {/* Selected Actions */}
      {selectedRows.size > 0 && (
        <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
          <span className="text-sm text-muted-foreground">
            {selectedRows.size} {selectedRows.size === 1 ? 'item' : 'items'} selected
          </span>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm">
              <Edit className="h-3 w-3 mr-2" />
              Edit
            </Button>
            <Button variant="outline" size="sm">
              <Trash2 className="h-3 w-3 mr-2" />
              Delete
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setSelectedRows(new Set())}
            >
              Clear
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}