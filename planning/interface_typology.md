# Interface Parameter Typology

## Overview
This document defines the standard parameter types available in the InteractiveViewer system and their corresponding GUI components. Each parameter type is designed for specific use cases and includes appropriate validation and constraints.

## Parameter Types

| Parameter Type | Description | GUI Component | Example Use Cases | Validation |
|---------------|-------------|---------------|-------------------|------------|
| Text | Free-form text input for labels and annotations | Text input field | Plot titles, axis labels, legend entries | String conversion |
| Single Selection | Choice from a predefined set of options | Dropdown menu | Dictionary keys, plot types, categorical variables | Value must be in options list |
| Multiple Selection | Selection of any number of items from a fixed set | Multi-select dropdown with checkboxes | Column selection for plotting, categories to include, line selection | All values must be in options list |
| Boolean | True/false toggle | Checkbox | Show/hide grid, enable features, log/linear scaling | Boolean conversion |
| Integer | Whole number within a specific range | Number input (step=1) with min/max | Array indices, bin counts, iteration numbers | Range validation, integer conversion |
| Float | Decimal number within a specific range | Number input with decimal support | Threshold values, filter parameters, scaling factors | Range validation, float conversion |
| Integer Pair | Two related integers, often defining a range | Two adjacent integer inputs | Array slice indices, histogram bins, iteration ranges | Range validation for both values |
| Float Pair | Two related floats, often defining a range | Two adjacent float inputs | Value ranges, coordinate ranges, confidence intervals | Range validation for both values |

## Implementation Details

### Common Properties
All parameter types share these common properties:
- Name (unique identifier)
- Default value(s)
- Validation rules
- Type checking

### Type-Specific Properties

#### Text
- Default: Empty string ("")
- Validation: Converts input to string

#### Single Selection
- Options list (required)
- Default: First option if not specified
- Validation: Value must be in options list

#### Multiple Selection
- Options list (required)
- Default: Empty list if not specified
- Validation: All selected values must be in options list

#### Boolean
- Default: False
- Validation: Converts input to boolean

#### Integer
- Minimum value (required)
- Maximum value (required)
- Default: Minimum value if not specified
- Validation: Range checking and integer conversion

#### Float
- Minimum value (required)
- Maximum value (required)
- Step size (default: 0.1)
- Default: Minimum value if not specified
- Validation: Range checking and float conversion

#### Integer Pair
- Minimum value (required)
- Maximum value (required)
- Default low value (optional)
- Default high value (optional)
- Validation: Range checking for both values

#### Float Pair
- Minimum value (required)
- Maximum value (required)
- Step size (default: 0.1)
- Default low value (optional)
- Default high value (optional)
- Validation: Range checking for both values

## Usage Guidelines

### Parameter Naming
- Use clear, descriptive names
- Follow snake_case convention
- Avoid overly long names
- Examples: "num_bins", "threshold", "show_grid"

### Default Values
- Choose sensible defaults that work for most cases
- Document any assumptions about defaults
- Consider the parameter's typical use case

### Value Ranges
- Set logical min/max values
- Consider practical limits
- Document range choices
- Example: opacity should be 0.0 to 1.0

### Validation
- All parameters validate their inputs
- Invalid values are either:
  - Clamped to valid range (numeric types)
  - Converted to correct type (text, boolean)
  - Rejected with ValueError (selection types)

## Best Practices

1. Type Selection:
- Use the most restrictive type that meets requirements
- Prefer single selection over text for known options
- Use pairs for related numeric values

2. Validation:
- Always validate parameter values
- Provide clear error messages
- Handle edge cases gracefully

3. Dependencies:
- Consider parameter relationships
- Use callbacks for updates
- Maintain consistent state

4. Documentation:
- Document parameter purposes
- Explain validation rules
- Provide usage examples