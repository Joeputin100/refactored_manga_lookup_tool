# Edge Browser Text Color Issue Analysis

## Problem Description
The user reported that the app text appears white in Chrome and Firefox (correct), but appears dark gray in Edge on Windows 11 and is hard to see.

## Current CSS Analysis

### App Styling (app_new_workflow.py lines 1761-1813)

The current CSS includes:

```css
/* Sidebar styling - black background */
section[data-testid="stSidebar"] > div {
    background-color: #000000 !important;
}

/* Background styling - multiple fallback paths for Streamlit Cloud */
.stApp {
    background: linear-gradient(rgba(0,0,0,0), rgba(0,0,0,0)),
                url('./static/background.jpg'),
                url('app/static/background.jpg'),
                url('static/background.jpg');
    background-size: cover;
    background-attachment: fixed;
}

/* Custom header styling */
.main-header {
    display: flex;
    align-items: center;
    gap: 15px;
    margin-bottom: 20px;
}

/* Card styling */
.stContainer {
    background-color: rgba(255,255,255,0.95);
    border-radius: 10px;
    padding: 20px;
    margin: 10px 0;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}
```

### Text Color Issues in Edge

Edge browser may have different default text color handling or CSS parsing behavior. The issue could be:

1. **Inherited text color**: Edge may not properly inherit text colors from parent elements
2. **CSS specificity**: Edge may require more specific CSS selectors
3. **Transparency handling**: Edge may handle rgba() colors differently
4. **Background contrast**: The background image may not provide sufficient contrast in Edge

## Potential Solutions

### 1. Explicit Text Color Definitions
Add explicit text color rules for all text elements:

```css
/* Force white text for all main content */
.stApp, .stApp * {
    color: white !important;
}

/* Override for card content (should remain dark) */
.stContainer, .stContainer * {
    color: #333333 !important;
}
```

### 2. Edge-Specific CSS
Use CSS feature detection or browser-specific prefixes:

```css
/* Edge-specific text color fixes */
@supports (-ms-ime-align:auto) {
    /* Edge-specific styles */
    .stApp, .stApp * {
        color: white !important;
    }
}
```

### 3. Enhanced Background Contrast
Improve background contrast for better text visibility:

```css
/* Enhanced background with better contrast */
.stApp {
    background:
        linear-gradient(rgba(0,0,0,0.7), rgba(0,0,0,0.7)),
        url('./static/background.jpg'),
        url('app/static/background.jpg'),
        url('static/background.jpg');
    background-size: cover;
    background-attachment: fixed;
}
```

### 4. Streamlit Component-Specific Fixes
Target specific Streamlit components that may have different styling in Edge:

```css
/* Fix Streamlit component text colors in Edge */
.stMarkdown, .stText, .stButton, .stSelectbox, .stTextInput {
    color: white !important;
}

/* Ensure card content remains readable */
.stContainer .stMarkdown,
.stContainer .stText,
.stContainer .stButton,
.stContainer .stSelectbox,
.stContainer .stTextInput {
    color: #333333 !important;
}
```

## Recommended Implementation

The most robust solution would be to add explicit text color definitions for all text elements, with proper contrast between background and foreground elements.