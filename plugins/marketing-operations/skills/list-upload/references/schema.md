# Lead Field Schema — starting seed

**This file is a read-only seed. Do not edit it** — it ships inside the plugin, so a plugin
update overwrites it. The live version lives at `list-upload-knowledge/lead-schema.md` in the
working folder.

Standard fields below are the same in almost every Marketo and Salesforce instance. Custom
fields are not: they are named per organization, so their API names are `???` here. **Resolve
them from the connectors** — `getAllFieldsUsingGET` for Marketo, `getObjectSchema` /
`describeUsingGET` for Salesforce — and write what you find to the working-folder copy. Do the
same for any field in a CSV that isn't listed here at all: look it up, don't guess a name.

Picklist values below are examples from one organization's instance, not a standard. Salesforce's
`Industry` picklist in particular is admin-editable and most orgs customize it, so **read the
real values from the connector before writing any picklist field** and record them in the
working-folder copy.

## Standard fields

| Field | Marketo API Name | SFDC API Name | Data Type |
|---|---|---|---|
| First Name | `firstName` | `FirstName` | string |
| Last Name | `lastName` | `LastName` | string |
| Email | `email` | `Email` | email |
| Phone | `phone` | `Phone` | phone |
| Website | `website` | `Website` | url |
| Company Name | `company` | `Company` | string |
| Street | `address` | `Street` | text |
| City | `city` | `City` | string |
| State | `state` | `StateCode` | string |
| Postal Code | `postalCode` | `PostalCode` | string |
| Country | `country` | `CountryCode` | string |
| Industry | `industry` | `Industry` | picklist — values are org-specific, see below |
| Job Title | `title` | `Title` | string |
| Person Source | `leadSource` | `LeadSource` | string |

## Custom fields — API names must be resolved from the connectors

These are the fields this skill was built around. Treat the labels as *suggestions* for what to
look for; the API names are unknowable without reading the target instance. A field may also not
exist at all, in which case say so and leave the column out rather than inventing a destination.

| Field | Marketo API Name | SFDC API Name | Data Type |
|---|---|---|---|
| LinkedIn Profile | `???` | `???` | string |
| Annual Revenue Range | `???` | `???` | picklist |
| Employees Range | `???` | `???` | picklist |
| Personal Notes | `???` | `???` | — |
| Hot Lead | `???` | `???` | boolean |
| Person Source Detail | `???` | `???` | string |

---

## Example picklist values

Everything in this section is an example from one instance. Verify against the connector before
use; where the real values differ, the working-folder copy is the record of truth.

### Annual revenue range — example buckets

`$0-$1M` · `$1M-$10M` · `$10M-$50M` · `$50M-$100M` · `$100M-$250M` · `$250M-$500M` · `$500M-$1B` · `$1B-$10B` · `$10B+`

### Employees range — example buckets

`1-10` · `11-50` · `51-250` · `251-1K` · `1K-5K` · `5K-10K` · `10K-50K` · `50K-100K` · `100K+`

### Industry — Salesforce's standard picklist

These are the 32 values Salesforce ships on the `Industry` field, and what
`industry_mapping_cache.json` maps incoming values onto.

**The field is admin-editable and most orgs customize it.** Some replace the list wholesale —
a GICS-derived set with `Software`, `Retailing` and `Banks` in place of `Technology`, `Retail`
and `Banking` is a common one, and only 8 of its values overlap with the list below. So this
table is useful as a shape to expect, and useless as a set of values to write. Read the real
picklist from the connector.

One quirk worth knowing because it recurs across instances: where a label contains spaces, the
API value usually matches the label exactly. Customized orgs often diverge here — one has the
label "Not For Profit" against the API value `Not_For_Profit`, where the standard value is
"Not for Profit" for both. Check rather than assume.

| Label | API Value |
|---|---|
| Agriculture | `Agriculture` |
| Apparel | `Apparel` |
| Banking | `Banking` |
| Biotechnology | `Biotechnology` |
| Chemicals | `Chemicals` |
| Communications | `Communications` |
| Construction | `Construction` |
| Consulting | `Consulting` |
| Education | `Education` |
| Electronics | `Electronics` |
| Energy | `Energy` |
| Engineering | `Engineering` |
| Entertainment | `Entertainment` |
| Environmental | `Environmental` |
| Finance | `Finance` |
| Food & Beverage | `Food & Beverage` |
| Government | `Government` |
| Healthcare | `Healthcare` |
| Hospitality | `Hospitality` |
| Insurance | `Insurance` |
| Machinery | `Machinery` |
| Manufacturing | `Manufacturing` |
| Media | `Media` |
| Not for Profit | `Not for Profit` |
| Other | `Other` |
| Recreation | `Recreation` |
| Retail | `Retail` |
| Shipping | `Shipping` |
| Technology | `Technology` |
| Telecommunications | `Telecommunications` |
| Transportation | `Transportation` |
| Utilities | `Utilities` |
