# Pricing rules used by change_order.py

All rates in examples are SAMPLE values. Use the rates in the signed contract.

1. Extended price = quantity x unit price, rounded half up to the cent. Adds are
   positive, credits are negative.
2. Net material and net labor are the sums of their signed lines.
3. Subtotal = net material + net labor.
4. Markup = subtotal x markup percent, only when the subtotal is positive. A net credit
   is returned without markup.
5. Material tax = net material x tax percent, only when net material is positive.
6. This change order = subtotal + markup + material tax.
7. Revised contract sum = original contract sum + prior approved changes + this change
   order.
8. Schedule days is a whole number. Positive adds working days, negative removes them,
   zero means no change.

Worked sample (invented numbers): material add 110.00, material credit 60.00, labor add
420.00, markup 15 percent, tax 8 percent. Net material 50.00, net labor 420.00, subtotal
470.00, markup 70.50, tax 4.00, change order 544.50.
