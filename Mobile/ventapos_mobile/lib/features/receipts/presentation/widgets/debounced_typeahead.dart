import 'dart:async';
import 'package:flutter/material.dart';

class DebouncedTypeahead<T extends Object> extends StatefulWidget {
  final Future<List<T>> Function(String pattern) suggestionsCallback;
  final Widget Function(BuildContext context, T suggestion) itemBuilder;
  final void Function(T suggestion) onSuggestionSelected;
  final String Function(T) displayStringForOption;
  final InputDecoration? decoration;
  final String? initialValue;
  final TextInputAction? textInputAction;

  const DebouncedTypeahead({
    super.key,
    required this.suggestionsCallback,
    required this.itemBuilder,
    required this.onSuggestionSelected,
    required this.displayStringForOption,
    this.decoration,
    this.initialValue,
    this.textInputAction,
  });

  @override
  State<DebouncedTypeahead<T>> createState() => _DebouncedTypeaheadState<T>();
}

class _DebouncedTypeaheadState<T extends Object> extends State<DebouncedTypeahead<T>> {
  Timer? _debounceTimer;

  @override
  void dispose() {
    _debounceTimer?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Autocomplete<T>(
      initialValue: TextEditingValue(text: widget.initialValue ?? ''),
      displayStringForOption: widget.displayStringForOption,
      optionsBuilder: (TextEditingValue textEditingValue) async {
        if (textEditingValue.text.isEmpty) {
          return const Iterable.empty();
        }

        // Completer to handle async debouncing in optionsBuilder
        final completer = Completer<Iterable<T>>();

        if (_debounceTimer?.isActive ?? false) _debounceTimer!.cancel();
        _debounceTimer = Timer(const Duration(milliseconds: 300), () async {
          try {
            final suggestions = await widget.suggestionsCallback(textEditingValue.text);
            completer.complete(suggestions);
          } catch (e) {
            completer.complete([]);
          }
        });

        return completer.future;
      },
      onSelected: widget.onSuggestionSelected,
      fieldViewBuilder: (context, textEditingController, focusNode, onFieldSubmitted) {
        return TextField(
          controller: textEditingController,
          focusNode: focusNode,
          textInputAction: widget.textInputAction,
          onSubmitted: (String value) {
            onFieldSubmitted();
          },
          decoration: widget.decoration,
        );
      },
      optionsViewBuilder: (context, onSelected, options) {
        return Align(
          alignment: Alignment.topLeft,
          child: Material(
            elevation: 4.0,
            child: SizedBox(
              height: 200.0,
              width: MediaQuery.of(context).size.width - 32, // approx width
              child: ListView.builder(
                padding: EdgeInsets.zero,
                itemCount: options.length,
                itemBuilder: (BuildContext context, int index) {
                  final T option = options.elementAt(index);
                  return InkWell(
                    onTap: () {
                      onSelected(option);
                    },
                    child: widget.itemBuilder(context, option),
                  );
                },
              ),
            ),
          ),
        );
      },
    );
  }
}
