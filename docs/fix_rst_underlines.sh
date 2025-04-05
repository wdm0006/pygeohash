#!/bin/bash

# Function to fix underlines in a single file
fix_underlines() {
    local file="$1"
    local temp_file="${file}.tmp"
    local prev_line=""
    local line_num=0
    
    # Clear temp file if it exists
    > "$temp_file"
    
    while IFS= read -r line || [ -n "$line" ]; do
        ((line_num++))
        
        # If current line consists only of one of these characters, it might be an underline
        # Note: Using extended grep with a more precise pattern for RST header underlines
        # The pattern matches lines that contain only one type of character from the valid set
        if echo "$line" | grep -E '^(=+|-+|~+|\^+|"+|\.+|_+|\*+|\++|#+)$' > /dev/null; then
            # Get the character used for underlining (handle empty lines)
            if [ -n "$line" ]; then
                underline_char="${line:0:1}"
            else
                underline_char="-"  # Default to hyphen for empty lines that should be underlines
            fi
            
            # Get the length of the previous line (header)
            # Trim any trailing whitespace that might affect length
            prev_length=${#prev_line}
            
            # Only proceed if we have a valid header line
            if [ $prev_length -gt 0 ]; then
                # Create new underline of correct length
                new_underline=$(printf "%${prev_length}s" | tr " " "$underline_char")
                
                # Only replace if lengths don't match
                if [ "${#line}" != "$prev_length" ]; then
                    echo "Fixing underline in $file at line $line_num"
                    echo "  From: '$line'"
                    echo "    To: '$new_underline'"
                    line="$new_underline"
                fi
            fi
        fi
        
        # Store current line for next iteration
        prev_line="$line"
        
        # Write to temp file
        echo "$line" >> "$temp_file"
    done < "$file"
    
    # Replace original with fixed version if temp file exists and has content
    if [ -s "$temp_file" ]; then
        mv "$temp_file" "$file"
    else
        rm -f "$temp_file"
    fi
}

# Find all .rst files in source directory (relative to where script is run from)
find source -name "*.rst" -type f | while read -r file; do
    echo "Processing $file..."
    fix_underlines "$file"
done 